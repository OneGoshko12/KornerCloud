from django.db import models
import os

# Create your models here.

#  Files land in separate subdirectories so
#  the two buckets never mix on disk.
def cloud_files_path(instance, filename):
    """Stores to:  media/cloud_files/<filename>"""
    return os.path.join('cloud_files', filename)
 
 
def cloud_media_path(instance, filename):
    """Stores to:  media/cloud_media/<filename>"""
    return os.path.join('cloud_media', filename)


# ─────────────────────────────────────────────
#  CloudFile  —  Files page
#  Accepts any non-media file (zips, docs, etc.)

class CloudFile(models.Model):
    # The actual file on disk
    file = models.FileField(upload_to=cloud_files_path)
 
    # Original filename as the user uploaded it
    original_name = models.CharField(max_length=500)
 
    # Size in bytes — stored so it can be displayed without stat() calls
    size = models.PositiveBigIntegerField(default=0)
 
    uploaded_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-uploaded_at']     # newest first
        verbose_name      = 'Cloud File'
        verbose_name_plural = 'Cloud Files'
 
    def __str__(self):
        return self.original_name
 
    def delete(self, *args, **kwargs):
        """Remove the file from disk when the model record is deleted."""
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
 
    # ── Helpers used in templates / views ─────
 
    @property
    def size_display(self):
        """Human-readable file size (B / KB / MB / GB)."""
        size = self.size
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{size} B"
            size /= 1024
        return f"{size:.1f} TB"
 
    @property
    def extension(self):
        """Lowercase file extension without the dot, e.g. 'zip'."""
        _, ext = os.path.splitext(self.original_name)
        return ext.lstrip('.').lower()
 
 
# ─────────────────────────────────────────────
#  MediaFile  —  Media page
#  Accepts only media files (images, video, audio)

class MediaFile(models.Model):
    # The actual file on disk
    file = models.FileField(upload_to=cloud_media_path)
 
    # Original filename as the user uploaded it
    original_name = models.CharField(max_length=500)
 
    # Size in bytes
    size = models.PositiveBigIntegerField(default=0)
 
    # MIME type recorded on upload — used for inline preview decisions
    mime_type = models.CharField(max_length=128, blank=True, default='')
 
    uploaded_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name        = 'Media File'
        verbose_name_plural = 'Media Files'
 
    def __str__(self):
        return self.original_name
 
    def delete(self, *args, **kwargs):
        """Remove the file from disk when the model record is deleted."""
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
 
    # ── Helpers used in templates / views ─────
 
    @property
    def size_display(self):
        """Human-readable file size."""
        size = self.size
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{size} B"
            size /= 1024
        return f"{size:.1f} TB"
 
    @property
    def extension(self):
        """Lowercase file extension without the dot, e.g. 'mp4'."""
        _, ext = os.path.splitext(self.original_name)
        return ext.lstrip('.').lower()
 
    @property
    def is_image(self):
        return self.mime_type.startswith('image/')
 
    @property
    def is_video(self):
        return self.mime_type.startswith('video/')
 
    @property
    def is_audio(self):
        return self.mime_type.startswith('audio/')

