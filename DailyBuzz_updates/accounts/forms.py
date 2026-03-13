from datetime import date
import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from .models import CustomUser


class SignupStep1Form(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip()
        if not first_name:
            raise forms.ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()
        if not last_name:
            raise forms.ValidationError("Last name is required.")
        return last_name

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("Username is required.")
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise forms.ValidationError("Email is required.")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError("You must be at least 18 years old to register.")
        return dob


class SignupStep2Form(forms.Form):
    country = forms.ChoiceField(choices=CustomUser.COUNTRY_CHOICES)
    phone_code = forms.ChoiceField(choices=CustomUser.PHONE_CODE_CHOICES)
    phone_number = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    terms_accepted = forms.BooleanField()

    def clean_country(self):
        country = self.cleaned_data.get("country")
        if not country:
            raise forms.ValidationError("Please select a country.")
        return country

    def clean_phone_code(self):
        phone_code = self.cleaned_data.get("phone_code")
        if not phone_code:
            raise forms.ValidationError("Please select a phone code.")
        return phone_code

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number", "").strip()
        if not phone_number:
            raise forms.ValidationError("Phone number is required.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")
        return phone_number

    def clean_password(self):
        password = self.cleaned_data["password"]

        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", password):
            raise forms.ValidationError("Password must contain at least one number.")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise forms.ValidationError("Password must contain at least one special character.")

        return password

    def clean_confirm_password(self):
        confirm_password = self.cleaned_data.get("confirm_password")
        if not confirm_password:
            raise forms.ValidationError("Please confirm your password.")
        return confirm_password

    def clean_terms_accepted(self):
        terms_accepted = self.cleaned_data.get("terms_accepted")
        if not terms_accepted:
            raise forms.ValidationError("You must accept the terms and conditions.")
        return terms_accepted

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class EmailOrUsernameLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email", max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        username_input = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_input and password:
            user_obj = CustomUser.objects.filter(email__iexact=username_input).first()
            username_for_auth = user_obj.username if user_obj else username_input

            self.user_cache = authenticate(
                self.request,
                username=username_for_auth,
                password=password,
            )

            if self.user_cache is None:
                raise forms.ValidationError("Invalid username/email or password.")

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.email_verified and not user.is_superuser:
            raise forms.ValidationError(
                "Please verify your email before logging in.",
                code="email_not_verified",
            )


class VerifyEmailForm(forms.Form):
    code = forms.CharField(max_length=6)

    def clean_code(self):
        code = self.cleaned_data.get("code", "").strip()
        if not code:
            raise forms.ValidationError("Verification code is required.")
        if not code.isdigit():
            raise forms.ValidationError("Verification code must contain digits only.")
        if len(code) != 6:
            raise forms.ValidationError("Verification code must be 6 digits.")
        return code