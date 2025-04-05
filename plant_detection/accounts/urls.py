from django.urls import path
from .views import (
    SignUpView,
    ActivateView,
    CheckEmailView,
    SuccessView,
    custom_login_view,
    custom_logout,
    register,
    welcome_view,
    resend_activation 
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('activate/<uidb64>/<token>/', ActivateView.as_view(), name='activate'),
    path('check-email/', CheckEmailView.as_view(), name='check_email'),
    path('success/', SuccessView.as_view(), name='success'),

    # Login and Logout URLs
    path('', welcome_view, name='welcome'),  # Default landing page
    path('login/', custom_login_view, name='login'),
    path('logout/', custom_logout, name='logout'),
    path("register/", register, name="register"),

    # Password Reset URLs
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), 
         name='password_reset_complete'),
     path('resend-activation/', resend_activation, name='resend_activation'), 
]