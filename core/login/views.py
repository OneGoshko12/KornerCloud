import io
import base64

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()



# ─────────────────────────────────────────────
#  LOGIN  (Step 1 of authentication)
# ─────────────────────────────────────────────
def login_view(request):
    """
    Handles username + password validation.

    Outcomes:
      • Wrong credentials          → 'You type something wrong!'
      • Default password detected  → warning message + 'Ok' button → New Password page
      • Valid credentials          → store user in session → 2FA page
    """

    # Already fully authenticated (credentials + OTP) → skip to cloud
    if request.user.is_authenticated and request.user.is_verified():
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # ── Authenticate ───────────────────────────
        # authenticate() is always called — whether the username or password
        # is wrong — so axes counts every failed attempt by IP.
        # Wrong username and wrong password are both tracked identically.
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'You type something wrong!')
            return render(request, 'login/login.html')

        # ── Default password check ─────────────────
        if user.check_password(settings.DEFAULT_USER_PASSWORD):
            # Store pk so the New Password page knows who is changing
            request.session['pre_password_change_user_id'] = user.pk
            # force_password_change=True triggers the warning popup in the template
            return render(request, 'login/login.html', {'force_password_change': True})

        # ── Credentials valid, password already changed → proceed to 2FA
        request.session['pre_2fa_user_id'] = user.pk
        return redirect('login:two_fa')

    return render(request, 'login/login.html')


# ─────────────────────────────────────────────
#  NEW PASSWORD
def new_password_view(request):
    """
    Handles both flows:
      • Forced change  — user arrived here because default password was detected
            (session key 'pre_password_change_user_id' is set)
      • Optional change — user clicked the 'New Password' link on the login page
            (no session key — single-user system, resolved by username)

    Checks (in order):
      1. Old password is correct
      2. New password differs from old
      3. Confirm matches new
      4. New password passes Django's AUTH_PASSWORD_VALIDATORS
    """
    if request.method == 'POST':
        old_password     = request.POST.get('old_password', '')
        new_password     = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # ── Resolve the user ───────────────────────
        user_id = request.session.get('pre_password_change_user_id')
        if user_id:
            # Forced-change flow
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return redirect('login:login')
        else:
            # Optional flow — single-user system
            try:
                user = User.objects.get(username=settings.DEFAULT_USERNAME)
            except User.DoesNotExist:
                return redirect('login:login')

        # ── 1. Old password must be correct ────────
        if not user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
            return render(request, 'login/new_password.html')

        # ── 2. New password must differ from old ───
        if new_password == old_password:
            messages.error(request, 'New password must be different from the current one.')
            return render(request, 'login/new_password.html')

        # ── 3. Confirmation must match ─────────────
        if new_password != confirm_password:
            messages.error(request, 'New password and confirmation do not match.')
            return render(request, 'login/new_password.html')

        # ── 4. Django password policy ──────────────
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'login/new_password.html')

        # ── All checks passed → save ───────────────
        user.set_password(new_password)
        user.save()

        # Clean up session key (forced-change flow)
        request.session.pop('pre_password_change_user_id', None)

        messages.success(request, 'Password changed successfully! Please log in with your new password.')
        return redirect('login:login')

    return render(request, 'login/new_password.html')


# ─────────────────────────────────────────────
#  2FA  (Step 2 of authentication)
def two_fa_view(request):
    """
    Handles TOTP verification via Google Authenticator.

    First-ever visit:
      • Creates an unconfirmed TOTPDevice
      • Generates a QR code (base64 PNG) passed to the template
      • Template shows a one-time QR-code modal

    All subsequent visits:
      • No QR code — just the 6-digit input

    Valid token:
      • Confirms the device (if first time)
      • Fully logs the user in (Django session + OTP marker)
      • Redirects to cloud home
    """

    # Guard — must come through login_view first
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('login:login')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('login:login')

    # ── QR code (first-time only) ──────────────
    has_confirmed_device = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
    qr_b64 = None

    if not has_confirmed_device:
        # Get or create an unconfirmed device to generate the QR URI
        device, _ = TOTPDevice.objects.get_or_create(
            user=user,
            name='Google Authenticator',
            defaults={'confirmed': False},
        )
        # Build QR code as a base64-encoded PNG
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(device.config_url)  # otpauth:// URI — Google Authenticator reads this
        qr.make(fit=True)
        img    = qr.make_image()
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    # ── Token submission ───────────────────────
    if request.method == 'POST':
        token = request.POST.get('otp_token', '').strip()

        try:
            device = TOTPDevice.objects.get(user=user, name='Google Authenticator')
        except TOTPDevice.DoesNotExist:
            messages.error(request, 'No authenticator device found. Please refresh the page.')
            return render(request, 'login/two_fa.html', {
                'has_confirmed_device': has_confirmed_device,
                'qr_b64': qr_b64,
            })

        if device.verify_token(token):
            # First successful verification → confirm the device permanently
            if not device.confirmed:
                device.confirmed = True
                device.save()

            # Clean up the pre-auth session key
            request.session.pop('pre_2fa_user_id', None)

            # Fully log in:
            #   auth_login  → creates the standard Django session
            #   otp_login   → stamps the session as OTP-verified (needed by OTPMiddleware)
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            otp_login(request, device)

            return redirect(settings.LOGIN_REDIRECT_URL)

        # Wrong code
        messages.error(request, 'Invalid code. Please try again.')

    return render(request, 'login/two_fa.html', {
        'has_confirmed_device': has_confirmed_device,
        'qr_b64': qr_b64,
    })


# ─────────────────────────────────────────────
#  LOGOUT
def logout_view(request):
    """Clears session and redirects to login."""
    auth_logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)



# ─────────────────────────────────────────────
#  CSRF FAILURE
def csrf_failure_view(request, reason=''):
    """
    Replaces Django's built-in CSRF failure handler so it uses
    the custom 403.html instead of the default page.
    """
    return render(request, '403.html', status=403)
