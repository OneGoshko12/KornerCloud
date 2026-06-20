from django.urls import path
from . import views

app_name = 'cloud'

urlpatterns = [
    # ── Home ───────────────────────────────────────────────
    path('',                         views.home_view,                name='home'),

    # ── Files page ─────────────────────────────────────────
    path('files/',                   views.files_view,               name='files'),
    path('files/upload/',            views.upload_files_view,        name='upload_files'),
    path('files/download/<int:pk>/', views.download_file_view,       name='download_file'),
    path('files/download/',          views.download_files_bulk_view, name='download_files_bulk'),
    path('files/delete/',            views.delete_files_view,        name='delete_files'),

    # ── Media page ─────────────────────────────────────────
    path('media/',                   views.media_view,               name='media'),
    path('media/upload/',            views.upload_media_view,        name='upload_media'),
    path('media/serve/<int:pk>/',    views.serve_media_view,         name='serve_media'),
    path('media/download/<int:pk>/', views.download_media_view,      name='download_media'),
    path('media/download/',          views.download_media_bulk_view, name='download_media_bulk'),
    path('media/delete/',            views.delete_media_view,        name='delete_media'),
]