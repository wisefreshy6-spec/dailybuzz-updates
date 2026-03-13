import random
import uuid
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone

from dashboard.models import PremiumPayment

from .forms import (
    SignupStep1Form,
    SignupStep2Form,
    EmailOrUsernameLoginForm,
    VerifyEmailForm,
)
from .models import CustomUser, EmailVerificationCode


def home_view(request):
    return redirect('signup')


def signup_step1_view(request):
    if request.method == 'POST':
        form = SignupStep1Form(request.POST)
        if form.is_valid():
            request.session['signup_step1'] = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'date_of_birth': str(form.cleaned_data['date_of_birth']),
            }
            return redirect('signup_step2')
    else:
        form = SignupStep1Form()

    return render(request, 'accounts/signup_step1.html', {'form': form})


def signup_step2_view(request):
    step1_data = request.session.get('signup_step1')

    if not step1_data:
        messages.error(request, "Please complete step 1 first.")
        return redirect('signup')

    if request.method == 'POST':
        form = SignupStep2Form(request.POST)
        if form.is_valid():
            user = CustomUser.objects.create_user(
                username=step1_data['username'],
                email=step1_data['email'],
                first_name=step1_data['first_name'],
                last_name=step1_data['last_name'],
                date_of_birth=step1_data['date_of_birth'],
                country=form.cleaned_data['country'],
                phone_code=form.cleaned_data['phone_code'],
                phone_number=form.cleaned_data['phone_number'],
                terms_accepted=form.cleaned_data['terms_accepted'],
                password=form.cleaned_data['password'],
                is_active=True,
                email_verified=False,
            )

            code = str(random.randint(100000, 999999))

            EmailVerificationCode.objects.create(
                user=user,
                code=code,
                purpose='signup',
            )

            send_mail(
                subject='Daily Buzz Updates Email Verification Code',
                message=f'Your verification code is: {code}',
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

            request.session['verify_user_id'] = user.id
            request.session.pop('signup_step1', None)

            messages.success(request, "Account created. Check the terminal for your verification code.")
            return redirect('verify_email')
    else:
        form = SignupStep2Form()

    return render(request, 'accounts/signup_step2.html', {'form': form})


def verify_email_view(request):
    user_id = request.session.get('verify_user_id')

    if not user_id:
        messages.error(request, "No pending verification found.")
        return redirect('signup')

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('signup')

    if request.method == 'POST':
        form = VerifyEmailForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']

            verification = EmailVerificationCode.objects.filter(
                user=user,
                code=code,
                purpose='signup',
                is_used=False
            ).order_by('-created_at').first()

            if verification:
                verification.is_used = True
                verification.save()

                user.email_verified = True
                user.save()

                request.session.pop('verify_user_id', None)
                messages.success(request, "Email verified successfully. You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Invalid verification code.")
    else:
        form = VerifyEmailForm()

    return render(request, 'accounts/verify_email.html', {
        'form': form,
        'user_email': user.email
    })


def resend_verification_code_view(request):
    user_id = request.session.get('verify_user_id')

    if not user_id:
        messages.error(request, "No verification session found.")
        return redirect('signup')

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('signup')

    code = str(random.randint(100000, 999999))

    EmailVerificationCode.objects.create(
        user=user,
        code=code,
        purpose='signup',
    )

    send_mail(
        subject='Daily Buzz Updates New Verification Code',
        message=f'Your new verification code is: {code}',
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )

    messages.success(request, "A new verification code has been sent.")
    return redirect('verify_email')


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = EmailOrUsernameLoginForm
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def premium_page_view(request):
    if not request.user.is_premium or request.user.premium_revoked:
        return render(request, "dashboard/premium_locked.html", {"user": request.user})
    return render(request, "dashboard/premium_page.html", {"user": request.user})

@login_required
def premium_success_view(request):
    return render(request, 'dashboard/premium_success.html', {'user': request.user})


@login_required
def start_premium_payment_view(request):
    if request.user.is_premium:
        messages.info(request, "Your premium membership is already active.")
        return redirect('premium_page')

    reference = f"premium-{request.user.id}-{uuid.uuid4().hex[:10]}"
    amount_kobo = int(settings.PREMIUM_PRICE_KES * 100)

    payment = PremiumPayment.objects.create(
        user=request.user,
        reference=reference,
        amount=settings.PREMIUM_PRICE_KES,
        currency='KES',
        status='pending',
        provider='paystack',
    )

    callback_url = request.build_absolute_uri('/accounts/premium/verify/')

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": request.user.email,
        "amount": amount_kobo,
        "reference": reference,
        "callback_url": callback_url,
        "currency": "KES",
        "metadata": {
            "user_id": request.user.id,
            "payment_type": "premium_upgrade",
        }
    }

    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response_data = response.json()
    except Exception:
        payment.status = 'failed'
        payment.save()
        messages.error(request, "Unable to connect to payment gateway right now.")
        return redirect('premium_page')

    if response.status_code == 200 and response_data.get("status") is True:
        auth_url = response_data["data"]["authorization_url"]
        return redirect(auth_url)

    payment.status = 'failed'
    payment.save()
    messages.error(request, "Failed to start premium payment.")
    return redirect('premium_page')


def terms_view(request):
    return render(request, 'accounts/terms.html')


@login_required
def verify_premium_payment_view(request):
    reference = request.GET.get("reference")

    if not reference:
        messages.error(request, "Missing payment reference.")
        return redirect('premium_page')

    try:
        payment = PremiumPayment.objects.get(reference=reference, user=request.user)
    except PremiumPayment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('premium_page')

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=30,
        )
        response_data = response.json()
    except Exception:
        messages.error(request, "Unable to verify payment right now.")
        return redirect('premium_page')

    if response.status_code == 200 and response_data.get("status") is True:
        data = response_data.get("data", {})
        gateway_status = data.get("status")

        if gateway_status == "success":
            payment.status = 'success'
            payment.paid_at = timezone.now()
            payment.save()

            request.user.is_premium = True
            request.user.premium_since = timezone.now()
            request.user.save()

            messages.success(request, "Premium access activated successfully.")
            return redirect('premium_success')

    payment.status = 'failed'
    payment.save()
    messages.error(request, "Payment was not successful.")
    return redirect('premium_page')
