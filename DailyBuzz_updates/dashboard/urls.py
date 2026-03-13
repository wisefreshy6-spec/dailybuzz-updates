from django.urls import path
from .views import (
    admin_news_create_view,
    admin_news_delete_view,
    admin_news_edit_view,
    admin_news_list_view,
    admin_support_detail_view,
    admin_support_list_view,
    creator_dashboard_view,
    dashboard_home,
    news_category_view,
    news_detail_view,
    news_search_view,
    notification_read_view,
    notifications_mark_all_read_view,
    notifications_view,
    profile_view,
    push_public_key_view,
    request_delete_account_view,
    request_password_change_view,
    request_phone_change_view,
    save_push_subscription_view,
    security_view,
    submit_content_view,
    support_center_view,
    support_ticket_detail_view,
    trending_news_view,
    verify_delete_account_view,
    verify_password_change_view,
    verify_phone_change_view,
)

urlpatterns = [
    path('', dashboard_home, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('security/', security_view, name='security'),

    path('news/<str:category>/', news_category_view, name='news_category'),
    path('post/<int:post_id>/', news_detail_view, name='news_detail'),
    path('search/', news_search_view, name='news_search'),
    path('trending/', trending_news_view, name='trending_news'),

    path('support/', support_center_view, name='support_center'),
    path('support/ticket/<int:ticket_id>/', support_ticket_detail_view, name='support_ticket_detail'),
    path('admin/support/', admin_support_list_view, name='admin_support_list'),
    path('admin/support/<int:ticket_id>/', admin_support_detail_view, name='admin_support_detail'),

    path('security/change-password/', request_password_change_view, name='request_password_change'),
    path('security/verify-password/', verify_password_change_view, name='verify_password_change'),

    path('security/change-phone/', request_phone_change_view, name='request_phone_change'),
    path('security/verify-phone/', verify_phone_change_view, name='verify_phone_change'),

    path('security/delete-account/', request_delete_account_view, name='request_delete_account'),
    path('security/verify-delete-account/', verify_delete_account_view, name='verify_delete_account'),

    path('admin/news/', admin_news_list_view, name='admin_news_list'),
    path('admin/news/add/', admin_news_create_view, name='admin_news_add'),
    path('admin/news/<int:post_id>/edit/', admin_news_edit_view, name='admin_news_edit'),
    path('admin/news/<int:post_id>/delete/', admin_news_delete_view, name='admin_news_delete'),

    path('push/public-key/', push_public_key_view, name='push_public_key'),
    path('push/save-subscription/', save_push_subscription_view, name='save_push_subscription'),

    path('submit/', submit_content_view, name='submit_content'),
    path('creator/', creator_dashboard_view, name='creator_dashboard'),

    path('notifications/', notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', notification_read_view, name='notification_read'),
    path('notifications/mark-all-read/', notifications_mark_all_read_view, name='notifications_mark_all_read'),
]