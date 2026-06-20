from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_user(apps, schema_editor):
    """
    Creates the default YouKnow user with the default password.
    Uses apps.get_model() instead of importing User directly —
    this is the correct way to access models inside migrations,
    so the migration stays stable even if the User model changes later.
    """
    User = apps.get_model('auth', 'User')

    # Only create if not already there — safe to run multiple times
    if not User.objects.filter(username='YouKnow').exists():
        User.objects.create(
            username='YouKnow',
            password=make_password('YouKnow12?'),
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )


def delete_default_user(apps, schema_editor):
    """
    Reverse migration — removes the user if rolling back.
    """
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='YouKnow').delete()


class Migration(migrations.Migration):
 
    # login has no 0001_initial (models.py is empty), so we only
    # depend on auth — the User table must exist before we insert into it
    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_default_user,    # forward
            delete_default_user,    # reverse (migrate --backwards)
        ),
    ]
