from django.contrib import admin
from django.utils import timezone

from .models import (
    SiteSetting,
    NewsPost,
    PremiumPayment,
    SupportTicket,
    SupportMessage,
    PushSubscription,
    UserSubmission,
    VideoPost,
    Notification,
)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'support_email')


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'is_published',
        'is_featured',
        'is_breaking',
        'show_in_carousel',
        'show_as_popup',
        'created_at',
    )
    list_filter = (
        'category',
        'is_published',
        'is_featured',
        'is_breaking',
        'show_in_carousel',
        'show_as_popup',
        'created_at',
    )
    search_fields = ('title', 'summary', 'content', 'editor_name')


@admin.register(PremiumPayment)
class PremiumPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'reference',
        'amount',
        'currency',
        'status',
        'provider',
        'created_at',
        'paid_at',
    )
    list_filter = ('status', 'provider', 'currency', 'created_at')
    search_fields = ('user__username', 'user__email', 'reference')
    actions = ['mark_success_and_enable_premium', 'mark_failed', 'revoke_user_premium']

    @admin.action(description='Mark selected payments as success and enable premium')
    def mark_success_and_enable_premium(self, request, queryset):
        for payment in queryset:
            payment.status = 'success'
            if not payment.paid_at:
                payment.paid_at = timezone.now()
            payment.save()

            user = payment.user
            user.is_premium = True
            user.premium_revoked = False
            user.premium_revoke_reason = ''
            if not user.premium_since:
                user.premium_since = timezone.now()
            user.save()

    @admin.action(description='Mark selected payments as failed')
    def mark_failed(self, request, queryset):
        queryset.update(status='failed')

    @admin.action(description='Revoke premium for selected payments users')
    def revoke_user_premium(self, request, queryset):
        for payment in queryset:
            user = payment.user
            user.is_premium = False
            user.premium_revoked = True
            user.premium_revoke_reason = 'Revoked by admin from payment admin'
            user.save()


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'user', 'issue_type', 'status', 'escalated_to_human', 'created_at')


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'sender', 'created_at')


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at')


@admin.register(UserSubmission)
class UserSubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'submission_type', 'category', 'status', 'created_at')
    list_filter = ('submission_type', 'category', 'status', 'created_at')
    search_fields = ('title', 'summary', 'user__username', 'user__email')
    actions = ['approve_submissions', 'reject_submissions']

    @admin.action(description='Approve selected submissions')
    def approve_submissions(self, request, queryset):
        for submission in queryset:
            submission.status = 'approved'
            submission.save()

            Notification.objects.create(
                user=submission.user,
                title='Submission approved',
                message=f'Your "{submission.title}" has been approved and published.'
            )

            if submission.submission_type == 'news':
                NewsPost.objects.create(
                    title=submission.title,
                    category=submission.category,
                    editor_name=submission.user.username,
                    summary=submission.summary,
                    content=submission.content,
                    image=submission.cover_image,
                    is_published=True,
                )

            elif submission.submission_type == 'video' and submission.video_file:
                VideoPost.objects.create(
                    title=submission.title,
                    category=submission.category,
                    creator_name=submission.user.username,
                    summary=submission.summary,
                    cover_image=submission.cover_image,
                    video_file=submission.video_file,
                    is_published=True,
                )

    @admin.action(description='Reject selected submissions')
    def reject_submissions(self, request, queryset):
        for submission in queryset:
            submission.status = 'rejected'
            submission.save()

            Notification.objects.create(
                user=submission.user,
                title='Submission rejected',
                message=f'Your "{submission.title}" was rejected by admin review.'
            )


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'creator_name', 'is_published', 'created_at')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'summary', 'creator_name')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')