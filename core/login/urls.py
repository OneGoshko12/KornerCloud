from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    path('',             views.login_view,       name='login'),
    path('new-password/', views.new_password_view, name='new_password'),
    path('2fa/',          views.two_fa_view,      name='two_fa'),
    path('logout/',       views.logout_view,      name='logout'),
]