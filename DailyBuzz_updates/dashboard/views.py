import json
import random
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from pywebpush import WebPushException, webpush

from accounts.models import EmailVerificationCode
from .forms import (
    DeleteAccountRequestForm,
    DeleteAccountVerifyForm,
    PasswordChangeRequestForm,
    PasswordOTPVerifyForm,
    PhoneChangeRequestForm,
    PhoneOTPVerifyForm,
)
from .models import (
    NewsPost,
    Notification,
    PushSubscription,
    SiteSetting,
    SupportMessage,
    SupportTicket,
)
from .news_forms import NewsPostForm
from .submission_forms import UserSubmissionForm
from .support_forms import SupportReplyForm, SupportRequestForm, TicketStatusForm


@login_required
def dashboard_home(request):
    site_settings = SiteSetting.objects.first()
    featured_post = NewsPost.objects.filter(is_published=True, is_featured=True).first()
    breaking_posts = NewsPost.objects.filter(is_published=True, is_breaking=True)[:8]
    latest_posts = NewsPost.objects.filter(is_published=True)[:8]
    carousel_posts = NewsPost.objects.filter(is_published=True, show_in_carousel=True)[:5]
    popup_post = NewsPost.objects.filter(
        is_published=True,
        is_breaking=True,
        show_as_popup=True
    ).first()

    unread_notifications_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    creator_submissions_count = request.user.submissions.count() if hasattr(request.user, 'submissions') else 0
    open_tickets_count = SupportTicket.objects.filter(user=request.user).exclude(status='closed').count()

    if popup_post:
        send_push_to_user(
            request.user,
            title=f"Breaking News: {popup_post.title}",
            body=popup_post.summary[:120],
            url=f"/dashboard/post/{popup_post.id}/"
        )

    return render(request, 'dashboard/dashboard.html', {
        'user': request.user,
        'site_settings': site_settings,
        'featured_post': featured_post,
        'breaking_posts': breaking_posts,
        'latest_posts': latest_posts,
        'carousel_posts': carousel_posts,
        'popup_post': popup_post,
        'unread_notifications_count': unread_notifications_count,
        'creator_submissions_count': creator_submissions_count,
        'open_tickets_count': open_tickets_count,
    })


@login_required
def news_search_view(request):
    site_settings = SiteSetting.objects.first()
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    posts = NewsPost.objects.filter(is_published=True)

    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query) |
            Q(editor_name__icontains=query)
        )

    if category:
        posts = posts.filter(category=category)

    return render(request, 'dashboard/news_search.html', {
        'site_settings': site_settings,
        'posts': posts,
        'query': query,
        'selected_category': category,
    })


@login_required
def profile_view(request):
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "dashboard/profile.html", {
        "user": request.user,
        "unread_notifications_count": unread_notifications_count,
    })


@login_required
def security_view(request):
    password_form = PasswordChangeRequestForm(request.user)
    phone_form = PhoneChangeRequestForm(request.user.PHONE_CODE_CHOICES)
    delete_form = DeleteAccountRequestForm(request.user)
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, "dashboard/security.html", {
        "user": request.user,
        "password_form": password_form,
        "phone_form": phone_form,
        "delete_form": delete_form,
        "unread_notifications_count": unread_notifications_count,
    })


@login_required
def news_category_view(request, category):
    site_settings = SiteSetting.objects.first()
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    posts = NewsPost.objects.filter(category=category, is_published=True)

    category_map = {
        "entertainment": "Entertainment",
        "sports": "Sports",
        "politics": "Politics",
        "technology": "Technology",
        "business": "Business",
        "health": "Health",
    }

    return render(request, "dashboard/news_category.html", {
        "posts": posts,
        "category": category,
        "category_name": category_map.get(category, category.title()),
        "site_settings": site_settings,
        "unread_notifications_count": unread_notifications_count,
    })


@login_required
def news_detail_view(request, post_id):
    site_settings = SiteSetting.objects.first()
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    post = get_object_or_404(NewsPost, id=post_id, is_published=True)
    post.views_count += 1
    post.save(update_fields=['views_count'])

    related_posts = NewsPost.objects.filter(
        category=post.category,
        is_published=True
    ).exclude(id=post.id)[:4]

    article_url = request.build_absolute_uri()

    return render(request, 'dashboard/news_detail.html', {
        'site_settings': site_settings,
        'post': post,
        'related_posts': related_posts,
        'article_url': article_url,
        'unread_notifications_count': unread_notifications_count,
    })


@login_required
def request_password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeRequestForm(request.user, request.POST)

        if form.is_valid():
            code = str(random.randint(100000, 999999))

            EmailVerificationCode.objects.create(
                user=request.user,
                code=code,
                purpose="password_change",
            )

            request.session["pending_new_password"] = form.cleaned_data["new_password"]

            send_mail(
                subject="Daily Buzz Updates Password Change Code",
                message=f"Your password change code is: {code}",
                from_email=None,
                recipient_list=[request.user.email],
                fail_silently=False,
            )

            messages.success(request, "Verification code sent to your email.")
            return redirect("verify_password_change")

    return redirect("security")


@login_required
def verify_password_change_view(request):
    form = PasswordOTPVerifyForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]

        verification = EmailVerificationCode.objects.filter(
            user=request.user,
            code=code,
            purpose="password_change",
            is_used=False,
        ).first()

        if verification:
            new_password = request.session.get("pending_new_password")

            request.user.set_password(new_password)
            request.user.save()

            update_session_auth_hash(request, request.user)

            verification.is_used = True
            verification.save()

            messages.success(request, "Password changed successfully.")
            return redirect("security")

    return render(request, "dashboard/verify_password_change.html", {"form": form})


@login_required
def request_phone_change_view(request):
    form = PhoneChangeRequestForm(request.user.PHONE_CODE_CHOICES, request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = str(random.randint(100000, 999999))

        EmailVerificationCode.objects.create(
            user=request.user,
            code=code,
            purpose="phone_change",
        )

        request.session["pending_new_phone_code"] = form.cleaned_data["new_phone_code"]
        request.session["pending_new_phone_number"] = form.cleaned_data["new_phone_number"]

        print("PHONE OTP:", code)

        messages.success(request, "Verification code generated. Check terminal.")
        return redirect("verify_phone_change")

    return redirect("security")


@login_required
def verify_phone_change_view(request):
    form = PhoneOTPVerifyForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]

        verification = EmailVerificationCode.objects.filter(
            user=request.user,
            code=code,
            purpose="phone_change",
            is_used=False,
        ).first()

        if verification:
            request.user.phone_code = request.session.get("pending_new_phone_code")
            request.user.phone_number = request.session.get("pending_new_phone_number")
            request.user.save()

            verification.is_used = True
            verification.save()

            messages.success(request, "Phone updated successfully.")
            return redirect("security")

    return render(request, "dashboard/verify_phone_change.html", {"form": form})


@login_required
def request_delete_account_view(request):
    form = DeleteAccountRequestForm(request.user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = str(random.randint(100000, 999999))

        EmailVerificationCode.objects.create(
            user=request.user,
            code=code,
            purpose="delete_account",
        )

        send_mail(
            subject="Delete Account Verification",
            message=f"Your delete code: {code}",
            from_email=None,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        messages.success(request, "Delete code sent to your email.")
        return redirect("verify_delete_account")

    return redirect("security")


@login_required
def verify_delete_account_view(request):
    form = DeleteAccountVerifyForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]

        verification = EmailVerificationCode.objects.filter(
            user=request.user,
            code=code,
            purpose="delete_account",
            is_used=False,
        ).first()

        if verification:
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Account deleted.")
            return redirect("signup")

    return render(request, "dashboard/verify_delete_account.html", {"form": form})


@staff_member_required
def admin_news_list_view(request):
    posts = NewsPost.objects.all()
    return render(request, "dashboard/admin_news_list.html", {"posts": posts})


@staff_member_required
def admin_news_create_view(request):
    form = NewsPostForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "News created.")
        return redirect("admin_news_list")

    return render(request, "dashboard/admin_news_form.html", {
        "form": form,
        "page_title": "Add News",
    })


@staff_member_required
def admin_news_edit_view(request, post_id):
    post = get_object_or_404(NewsPost, id=post_id)
    form = NewsPostForm(request.POST or None, request.FILES or None, instance=post)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "News updated.")
        return redirect("admin_news_list")

    return render(request, "dashboard/admin_news_form.html", {
        "form": form,
        "page_title": "Edit News",
    })


@staff_member_required
def admin_news_delete_view(request, post_id):
    post = get_object_or_404(NewsPost, id=post_id)

    if request.method == "POST":
        post.delete()
        messages.success(request, "News deleted.")
        return redirect("admin_news_list")

    return render(request, "dashboard/admin_news_delete.html", {"post": post})


@login_required
def support_center_view(request):
    form = SupportRequestForm(request.POST or None)
    recent_tickets = SupportTicket.objects.filter(user=request.user)[:8]
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    if request.method == 'POST' and form.is_valid():
        issue_type = form.cleaned_data['issue_type']
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']
        escalate = form.cleaned_data['escalate_to_human']

        ai_reply = generate_ai_support_reply(issue_type, message)
        case_number = f"DBU-{uuid.uuid4().hex[:8].upper()}"

        ticket = SupportTicket.objects.create(
            user=request.user,
            case_number=case_number,
            issue_type=issue_type,
            subject=subject,
            message=message,
            ai_response=ai_reply['response'],
            escalated_to_human=(escalate or ai_reply.get('needs_human', False)),
            status='open',
            admin_unread_count=1,
        )

        SupportMessage.objects.create(ticket=ticket, sender='user', message=message)
        SupportMessage.objects.create(ticket=ticket, sender='ai', message=ai_reply['response'])

        if ticket.escalated_to_human:
            send_mail(
                subject=f"New Support Case {case_number}",
                message=(
                    f"Case Number: {case_number}\n"
                    f"User: {request.user.username}\n"
                    f"Email: {request.user.email}\n"
                    f"Issue Type: {issue_type}\n"
                    f"Subject: {subject}\n\n"
                    f"Message:\n{message}\n\n"
                    f"AI Response:\n{ai_reply['response']}"
                ),
                from_email=None,
                recipient_list=['dupdateske@gmail.com'],
                fail_silently=True,
            )

        Notification.objects.create(
            user=request.user,
            title="Support case created",
            message=f"Your support case {case_number} has been created successfully."
        )

        messages.success(request, f"Support request created. Case number: {case_number}")
        return redirect('support_ticket_detail', ticket_id=ticket.id)

    return render(request, 'dashboard/support_center.html', {
        'form': form,
        'recent_tickets': recent_tickets,
        'unread_notifications_count': unread_notifications_count,
    })


@login_required
def support_ticket_detail_view(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    reply_form = SupportReplyForm(request.POST or None, request.FILES or None)
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    if ticket.user_unread_count > 0:
        ticket.user_unread_count = 0
        ticket.save()

    if request.method == 'POST' and reply_form.is_valid():
        text = reply_form.cleaned_data['message']
        attachment = reply_form.cleaned_data.get('attachment')

        SupportMessage.objects.create(
            ticket=ticket,
            sender='user',
            message=text or '',
            attachment=attachment,
        )

        ticket.admin_unread_count += 1
        ticket.status = 'in_progress'
        ticket.save()

        if text:
            ai_reply = generate_ai_support_reply(ticket.issue_type, text)

            SupportMessage.objects.create(
                ticket=ticket,
                sender='ai',
                message=ai_reply['response'],
            )

            ticket.user_unread_count += 1

            if ai_reply.get('needs_human', False):
                ticket.escalated_to_human = True

            ticket.save()

        messages.success(request, "Message sent.")
        return redirect('support_ticket_detail', ticket_id=ticket.id)

    return render(request, 'dashboard/support_ticket_detail.html', {
        'ticket': ticket,
        'reply_form': reply_form,
        'unread_notifications_count': unread_notifications_count,
    })


@staff_member_required
def admin_support_list_view(request):
    tickets = SupportTicket.objects.all()
    return render(request, 'dashboard/admin_support_list.html', {'tickets': tickets})


@staff_member_required
def admin_support_detail_view(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    reply_form = SupportReplyForm(request.POST or None, request.FILES or None)
    status_form = TicketStatusForm(initial={'status': ticket.status})

    if ticket.admin_unread_count > 0:
        ticket.admin_unread_count = 0
        ticket.save()

    if request.method == 'POST':
        if 'send_reply' in request.POST:
            reply_form = SupportReplyForm(request.POST, request.FILES)
            if reply_form.is_valid():
                text = reply_form.cleaned_data['message']
                attachment = reply_form.cleaned_data.get('attachment')

                SupportMessage.objects.create(
                    ticket=ticket,
                    sender='agent',
                    message=text or '',
                    attachment=attachment,
                )

                ticket.status = 'in_progress'
                ticket.escalated_to_human = True
                ticket.user_unread_count += 1
                ticket.save()

                Notification.objects.create(
                    user=ticket.user,
                    title="Support reply received",
                    message=f"You received a new reply on case {ticket.case_number}."
                )

                messages.success(request, "Agent reply sent.")
                return redirect('admin_support_detail', ticket_id=ticket.id)

        elif 'update_status' in request.POST:
            status_form = TicketStatusForm(request.POST)
            if status_form.is_valid():
                ticket.status = status_form.cleaned_data['status']
                ticket.save()
                messages.success(request, "Ticket status updated.")
                return redirect('admin_support_detail', ticket_id=ticket.id)

    return render(request, 'dashboard/admin_support_detail.html', {
        'ticket': ticket,
        'reply_form': reply_form,
        'status_form': status_form,
    })


def generate_ai_support_reply(issue_type, message):
    if issue_type == 'login':
        return {
            'response': (
                "Please confirm you are using the correct username or email and password. "
                "If you forgot your password, use the Forgot Password option on the login page. "
                "If your account is new, ensure your email has been verified first."
            ),
            'needs_human': False,
        }

    if issue_type == 'password':
        return {
            'response': (
                "Use the Forgot Password option if you cannot log in. "
                "If you are already signed in, go to Security and request a password change. "
                "A verification code should be sent before the password update is completed."
            ),
            'needs_human': False,
        }

    if issue_type == 'verification':
        return {
            'response': (
                "Please request a new verification code and make sure you are entering the latest code sent to your email."
            ),
            'needs_human': False,
        }

    if issue_type == 'payment':
        return {
            'response': (
                "For payment issues, first confirm whether the transaction completed successfully. "
                "If premium access did not activate after payment, this should be reviewed by a human agent."
            ),
            'needs_human': True,
        }

    if issue_type == 'phone':
        return {
            'response': (
                "Go to Security and request a phone number change. "
                "A verification code is required before the new number is saved."
            ),
            'needs_human': False,
        }

    if issue_type == 'account':
        return {
            'response': (
                "Security-sensitive account actions may require manual review. "
                "This case may need human support if the automated process does not complete successfully."
            ),
            'needs_human': True,
        }

    if issue_type == 'news':
        return {
            'response': (
                "Please include the article title, category, or exact issue with the news content. "
                "A human editor may need to review this."
            ),
            'needs_human': True,
        }

    return {
        'response': (
            "I could not fully resolve this automatically. "
            "This issue may need to be reviewed by a human support agent."
        ),
        'needs_human': True,
    }


@login_required
@csrf_exempt
def save_push_subscription_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)

        subscription = data.get("subscription", {})
        endpoint = subscription.get("endpoint")
        keys = subscription.get("keys", {})
        p256dh = keys.get("p256dh")
        auth = keys.get("auth")

        if not endpoint or not p256dh or not auth:
            return JsonResponse({"error": "Incomplete subscription data"}, status=400)

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "p256dh": p256dh,
                "auth": auth,
            }
        )

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def push_public_key_view(request):
    return JsonResponse({"publicKey": settings.VAPID_PUBLIC_KEY})


def send_push_to_user(user, title, body, url=None):
    subscriptions = PushSubscription.objects.filter(user=user)

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth,
            },
        }

        payload = json.dumps({
            "title": title,
            "body": body,
            "url": url or "/dashboard/",
        })

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": settings.VAPID_ADMIN_EMAIL,
                },
            )
        except WebPushException:
            pass


@login_required
def submit_content_view(request):
    form = UserSubmissionForm(request.POST or None, request.FILES or None)
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    if request.method == 'POST' and form.is_valid():
        submission = form.save(commit=False)
        submission.user = request.user
        submission.status = 'pending'
        submission.save()

        Notification.objects.create(
            user=request.user,
            title="Submission received",
            message=f'Your submission "{submission.title}" has been sent for admin review.'
        )

        messages.success(request, "Your submission has been sent for admin review.")
        return redirect('submit_content')

    return render(request, 'dashboard/submit_content.html', {
        'form': form,
        'user': request.user,
        'unread_notifications_count': unread_notifications_count,
    })


@login_required
def creator_dashboard_view(request):
    submissions = request.user.submissions.all().order_by('-created_at')
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    pending_count = submissions.filter(status='pending').count()
    approved_count = submissions.filter(status='approved').count()
    rejected_count = submissions.filter(status='rejected').count()

    return render(request, 'dashboard/creator_dashboard.html', {
        'user': request.user,
        'submissions': submissions,
        'unread_notifications_count': unread_notifications_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@login_required
def trending_news_view(request):
    site_settings = SiteSetting.objects.first()
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    posts = NewsPost.objects.filter(is_published=True).order_by('-views_count', '-created_at')[:20]
    return render(request, 'dashboard/trending_news.html', {
        'posts': posts,
        'user': request.user,
        'site_settings': site_settings,
        'unread_notifications_count': unread_notifications_count,
    })


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_notifications_count = notifications.filter(is_read=False).count()

    return render(request, 'dashboard/notifications.html', {
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'user': request.user,
    })


@login_required
def notification_read_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')


@login_required
def notifications_mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications')