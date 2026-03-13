from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    COUNTRY_CHOICES = [
        ('KE', 'Kenya'),
        ('UG', 'Uganda'),
        ('TZ', 'Tanzania'),
        ('RW', 'Rwanda'),
        ('BI', 'Burundi'),
        ('ET', 'Ethiopia'),
        ('NG', 'Nigeria'),
        ('GH', 'Ghana'),
        ('ZA', 'South Africa'),
        ('US', 'United States'),
        ('UK', 'United Kingdom'),
        ('IN', 'India'),
        ('CA', 'Canada'),
    ]

    PHONE_CODE_CHOICES = [
        ('+254', 'Kenya (+254)'),
        ('+256', 'Uganda (+256)'),
        ('+255', 'Tanzania (+255)'),
        ('+250', 'Rwanda (+250)'),
        ('+257', 'Burundi (+257)'),
        ('+251', 'Ethiopia (+251)'),
        ('+234', 'Nigeria (+234)'),
        ('+233', 'Ghana (+233)'),
        ('+27', 'South Africa (+27)'),
        ('+1', 'USA/Canada (+1)'),
        ('+44', 'United Kingdom (+44)'),
        ('+91', 'India (+91)'),
    ]

    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=5, choices=COUNTRY_CHOICES, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone_code = models.CharField(max_length=6, choices=PHONE_CODE_CHOICES, blank=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^[0-9]+$', 'Phone number must contain digits only.')]
    )
    terms_accepted = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    is_premium = models.BooleanField(default=False)
    premium_since = models.DateTimeField(null=True, blank=True)
    premium_revoked = models.BooleanField(default=False)
    premium_revoke_reason = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.email_verified = True
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class EmailVerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('signup', 'Signup'),
        ('password_change', 'Password Change'),
        ('phone_change', 'Phone Change'),
        ('delete_account', 'Delete Account'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES, default='signup')
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.code} ({self.purpose})"