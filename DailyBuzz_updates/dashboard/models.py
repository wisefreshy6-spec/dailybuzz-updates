from django.db import models
from django.conf import settings


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=120, default='Daily Buzz Updates')
    site_tagline = models.CharField(max_length=200, default='Fast, smart, and reliable updates')
    logo = models.ImageField(upload_to='site_branding/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site_branding/', blank=True, null=True)
    homepage_banner_title = models.CharField(max_length=200, default='Welcome to Daily Buzz Updates')
    homepage_banner_subtitle = models.TextField(default='Stay informed with breaking news, featured reports, and premium stories.')
    support_email = models.EmailField(default='dupdateske@gmail.com')

    def __str__(self):
        return self.site_name


class NewsPost(models.Model):
    CATEGORY_CHOICES = [
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('politics', 'Politics'),
        ('technology', 'Technology'),
        ('business', 'Business'),
        ('health', 'Health'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    editor_name = models.CharField(max_length=120, default='Daily Buzz Editorial Desk')
    summary = models.TextField()
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_breaking = models.BooleanField(default=False)
    show_in_carousel = models.BooleanField(default=False)
    show_as_popup = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    def __str__(self):
        return self.title


class PremiumPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, unique=True)
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default='KES')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider = models.CharField(max_length=30, default='paystack')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.reference} - {self.status}"


class SupportTicket(models.Model):
    ISSUE_CHOICES = [
        ('login', 'Login Problem'),
        ('password', 'Password Reset'),
        ('verification', 'Email Verification'),
        ('payment', 'Payment / Premium'),
        ('phone', 'Phone Number Change'),
        ('account', 'Account Deletion / Security'),
        ('news', 'News / Content Issue'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case_number = models.CharField(max_length=30, unique=True)
    issue_type = models.CharField(max_length=30, choices=ISSUE_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    ai_response = models.TextField(blank=True)
    escalated_to_human = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    user_unread_count = models.PositiveIntegerField(default=0)
    admin_unread_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.case_number} - {self.user.username} - {self.issue_type}"


class SupportMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
        ('agent', 'Agent'),
    ]

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField(blank=True)
    attachment = models.FileField(upload_to='support_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.ticket.case_number} - {self.sender}"
    

class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )

    endpoint = models.URLField()
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} subscription"

class UserSubmission(models.Model):
    TYPE_CHOICES = [
        ('news', 'News Article'),
        ('video', 'Video'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    CATEGORY_CHOICES = [
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('politics', 'Politics'),
        ('technology', 'Technology'),
        ('business', 'Business'),
        ('health', 'Health'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    submission_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    content = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='submission_images/', blank=True, null=True)
    video_file = models.FileField(upload_to='submission_videos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
class VideoPost(models.Model):
    CATEGORY_CHOICES = [
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('politics', 'Politics'),
        ('technology', 'Technology'),
        ('business', 'Business'),
        ('health', 'Health'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    creator_name = models.CharField(max_length=150, blank=True)
    summary = models.TextField()
    cover_image = models.ImageField(upload_to='video_covers/', blank=True, null=True)
    video_file = models.FileField(upload_to='published_videos/')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
class Advertisement(models.Model):
    POSITION_CHOICES = [
        ('homepage_top', 'Homepage Top'),
        ('sidebar', 'Sidebar'),
        ('article_inline', 'Article Inline'),
        ('footer', 'Footer'),
    ]

    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='ads/')
    link = models.URLField(blank=True)
    position = models.CharField(max_length=30, choices=POSITION_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title