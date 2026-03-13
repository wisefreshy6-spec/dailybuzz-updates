from django.contrib import admin
from .models import CustomUser, EmailVerificationCode


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'is_staff',
        'is_premium',
        'premium_revoked',
        'email_verified',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_premium',
        'premium_revoked',
        'email_verified',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')

    actions = ['revoke_premium_access', 'restore_premium_access']

    @admin.action(description='Revoke premium access for selected users')
    def revoke_premium_access(self, request, queryset):
        queryset.update(
            is_premium=False,
            premium_revoked=True,
            premium_revoke_reason='Revoked by admin'
        )

    @admin.action(description='Restore premium access for selected users')
    def restore_premium_access(self, request, queryset):
        queryset.update(
            is_premium=True,
            premium_revoked=False,
            premium_revoke_reason=''
        )


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'purpose', 'created_at', 'is_used')
    list_filter = ('purpose', 'is_used', 'created_at')