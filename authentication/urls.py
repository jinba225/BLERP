"""
Authentication app URLs.
"""
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user-info/', views.user_info_view, name='user_info'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset-confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('refresh-token/', views.refresh_token_view, name='refresh_token'),
]