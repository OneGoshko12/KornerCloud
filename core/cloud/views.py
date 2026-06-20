import mimetypes
import os
import tempfile
import zipfile

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django_otp.decorators import otp_required

from .models import CloudFile, MediaFile


# ─────────────────────────────────────────────
#  Constants & helpers
# ─────────────────────────────────────────────


MEDIA_MIME_PREFIXES = ('image/', 'video/', 'audio/')


def _get_mime(upload) -> str:
    mime, _ = mimetypes.guess_type(upload.name)
    return mime or 'application/octet-stream'


def _is_media(mime: str) -> bool:
    return any(mime.startswith(p) for p in MEDIA_MIME_PREFIXES)


# ─────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────

@never_cache
@otp_required
def home_view(request):
    return render(request, 'cloud/home.html')


# ─────────────────────────────────────────────
#  FILES PAGE
# ─────────────────────────────────────────────

@never_cache
@otp_required
def files_view(request):
    files = CloudFile.objects.all()
    return render(request, 'cloud/files.html', {'files': files})


@otp_required
def upload_files_view(request):
    if request.method != 'POST':
        return redirect('cloud:files')

    uploads = request.FILES.getlist('files')
    if not uploads:
        messages.error(request, 'No files selected.')
        return redirect('cloud:files')

    accepted, rejected = [], []

    for upload in uploads:
        mime = _get_mime(upload)
        if _is_media(mime):
            rejected.append(upload.name)
            continue
        CloudFile.objects.create(
            file=upload,
            original_name=upload.name,
            size=upload.size,
        )
        accepted.append(upload.name)

    if accepted:
        messages.success(request, f"Uploaded: {', '.join(accepted)}")
    if rejected:
        messages.error(request, f"Rejected (media files belong on the Media page): {', '.join(rejected)}")

    return redirect('cloud:files')


@otp_required
def download_file_view(request, pk):
    cloud_file = get_object_or_404(CloudFile, pk=pk)
    if not os.path.isfile(cloud_file.file.path):
        raise Http404('File not found on disk.')
    return FileResponse(
        open(cloud_file.file.path, 'rb'),
        as_attachment=True,
        filename=cloud_file.original_name,
    )


@otp_required
def download_files_bulk_view(request):
    if request.method != 'POST':
        return redirect('cloud:files')

    ids = request.POST.getlist('file_ids')
    if not ids:
        messages.warning(request, 'No files selected for download.')
        return redirect('cloud:files')

    files = CloudFile.objects.filter(pk__in=ids)
    if not files.exists():
        messages.error(request, 'Selected files not found.')
        return redirect('cloud:files')

    if files.count() == 1:
        cf = files.first()
        if not os.path.isfile(cf.file.path):
            raise Http404('File not found on disk.')
        return FileResponse(
            open(cf.file.path, 'rb'),
            as_attachment=True,
            filename=cf.original_name,
        )

    tmp = tempfile.TemporaryFile()
    try:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_STORED, allowZip64=True) as zf:
            for cf in files:
                if os.path.isfile(cf.file.path):
                    zf.write(cf.file.path, arcname=cf.original_name)
        tmp.seek(0)
        return FileResponse(tmp, as_attachment=True, filename='kornercloud_files.zip')
    except Exception:
        tmp.close()
        messages.error(request, 'Failed to build zip. Check available disk space.')
        return redirect('cloud:files')


@otp_required
def delete_files_view(request):
    if request.method != 'POST':
        return redirect('cloud:files')

    ids = request.POST.getlist('file_ids')
    if not ids:
        messages.warning(request, 'No files selected for deletion.')
        return redirect('cloud:files')

    files = CloudFile.objects.filter(pk__in=ids)
    names = [f.original_name for f in files]
    count = len(names)
    for f in files:
        f.delete()

    messages.success(request, f"Deleted {count} file(s): {', '.join(names)}")
    return redirect('cloud:files')


# ─────────────────────────────────────────────
#  MEDIA PAGE
# ─────────────────────────────────────────────

@never_cache
@otp_required
def media_view(request):
    media_files = MediaFile.objects.all()
    return render(request, 'cloud/media.html', {'media_files': media_files})


@otp_required
def upload_media_view(request):
    if request.method != 'POST':
        return redirect('cloud:media')

    uploads = request.FILES.getlist('files')
    if not uploads:
        messages.error(request, 'No files selected.')
        return redirect('cloud:media')

    accepted, rejected = [], []

    for upload in uploads:
        mime = _get_mime(upload)
        if not _is_media(mime):
            rejected.append(upload.name)
            continue
        MediaFile.objects.create(
            file=upload,
            original_name=upload.name,
            size=upload.size,
            mime_type=mime,
        )
        accepted.append(upload.name)

    if accepted:
        messages.success(request, f"Uploaded: {', '.join(accepted)}")
    if rejected:
        messages.error(request, f"Rejected (non-media files belong on the Files page): {', '.join(rejected)}")

    return redirect('cloud:media')


@otp_required
def serve_media_view(request, pk):
    """
    Serves a MediaFile INLINE — used as the src for <img>, <video>, <audio>
    in the media grid and lightbox. No 'as_attachment' so the browser
    renders it directly rather than downloading it.
    Still requires full OTP authentication — no public access.
    """
    media_file = get_object_or_404(MediaFile, pk=pk)
    if not os.path.isfile(media_file.file.path):
        raise Http404('File not found on disk.')
    return FileResponse(
        open(media_file.file.path, 'rb'),
        as_attachment=False,
        content_type=media_file.mime_type or 'application/octet-stream',
    )


@otp_required
def download_media_view(request, pk):
    media_file = get_object_or_404(MediaFile, pk=pk)
    if not os.path.isfile(media_file.file.path):
        raise Http404('File not found on disk.')
    return FileResponse(
        open(media_file.file.path, 'rb'),
        as_attachment=True,
        filename=media_file.original_name,
    )


@otp_required
def download_media_bulk_view(request):
    if request.method != 'POST':
        return redirect('cloud:media')

    ids = request.POST.getlist('file_ids')
    if not ids:
        messages.warning(request, 'No files selected for download.')
        return redirect('cloud:media')

    files = MediaFile.objects.filter(pk__in=ids)
    if not files.exists():
        messages.error(request, 'Selected files not found.')
        return redirect('cloud:media')

    if files.count() == 1:
        mf = files.first()
        if not os.path.isfile(mf.file.path):
            raise Http404('File not found on disk.')
        return FileResponse(
            open(mf.file.path, 'rb'),
            as_attachment=True,
            filename=mf.original_name,
        )

    tmp = tempfile.TemporaryFile()
    try:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_STORED, allowZip64=True) as zf:
            for mf in files:
                if os.path.isfile(mf.file.path):
                    zf.write(mf.file.path, arcname=mf.original_name)
        tmp.seek(0)
        return FileResponse(tmp, as_attachment=True, filename='kornercloud_media.zip')
    except Exception:
        tmp.close()
        messages.error(request, 'Failed to build zip. Check available disk space.')
        return redirect('cloud:media')


@otp_required
def delete_media_view(request):
    if request.method != 'POST':
        return redirect('cloud:media')

    ids = request.POST.getlist('file_ids')
    if not ids:
        messages.warning(request, 'No files selected for deletion.')
        return redirect('cloud:media')

    files = MediaFile.objects.filter(pk__in=ids)
    names = [f.original_name for f in files]
    count = len(names)
    for f in files:
        f.delete()

    messages.success(request, f"Deleted {count} file(s): {', '.join(names)}")
    return redirect('cloud:media')

