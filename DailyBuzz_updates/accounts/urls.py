from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    home_view,
    signup_step1_view,
    signup_step2_view,
    verify_email_view,
    resend_verification_code_view,
    CustomLoginView,
    logout_view,
    premium_page_view,
    premium_success_view,
    start_premium_payment_view,
    verify_premium_payment_view,
    terms_view,
)

urlpatterns = [

    path('', home_view, name='home'),

    path('signup/', signup_step1_view, name='signup'),
    path('signup/step2/', signup_step2_view, name='signup_step2'),

    path('verify-email/', verify_email_view, name='verify_email'),
    path('resend-code/', resend_verification_code_view, name='resend_code'),

    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path(
    'password-reset/',
    auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password-reset/done/'
    ),
    name='password_reset'
),
path(
    'password-reset/done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ),
    name='password_reset_done'
),
path(
    'reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ),
    name='password_reset_confirm'
),
path(
    'reset/done/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ),
    name='password_reset_complete'
),

    path('terms/', terms_view, name='terms'),

    path('premium/', premium_page_view, name='premium_page'),
    path('premium/start/', start_premium_payment_view, name='start_premium_payment'),
    path('premium/verify/', verify_premium_payment_view, name='verify_premium_payment'),
    path('premium/success/', premium_success_view, name='premium_success'),

]