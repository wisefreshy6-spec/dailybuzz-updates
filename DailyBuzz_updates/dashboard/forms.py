import re
from django import forms


class PasswordChangeRequestForm(forms.Form):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput
    )
    confirm_new_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect.")
        return current_password

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')

        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password must contain at least one number.")
        if not re.search(r'[^A-Za-z0-9]', password):
            raise forms.ValidationError("Password must contain at least one special character.")

        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')

        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise forms.ValidationError("New passwords do not match.")

        return cleaned_data


class PasswordOTPVerifyForm(forms.Form):
    code = forms.CharField(max_length=6)

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Enter a valid 6-digit code.")
        return code


class PhoneChangeRequestForm(forms.Form):
    new_phone_code = forms.ChoiceField(choices=[])
    new_phone_number = forms.CharField(max_length=20)

    def __init__(self, phone_choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_phone_code'].choices = phone_choices

    def clean_new_phone_number(self):
        number = self.cleaned_data.get('new_phone_number', '').strip()
        if not number:
            raise forms.ValidationError("New phone number is required.")
        if not number.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")
        return number


class PhoneOTPVerifyForm(forms.Form):
    code = forms.CharField(max_length=6)

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Enter a valid 6-digit code.")
        return code


class DeleteAccountRequestForm(forms.Form):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput
    )
    confirm_delete = forms.BooleanField(
        label="I understand that deleting my account is permanent."
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect.")
        return current_password


class DeleteAccountVerifyForm(forms.Form):
    code = forms.CharField(max_length=6)

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Enter a valid 6-digit code.")
        return code