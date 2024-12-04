from django.urls import path
from . import views 
from django.urls import re_path
from .consumers import NotificationConsumer
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'), 
    path('create-post/', views.create_post, name='create_post'),
    path('chairman-profile/', views.chairman_profile, name='chairman_profile'),
    path('create_chairman_profile/', views.create_chairman_profile, name='create_chairman_profile'),
    path('edit-profile/', views.edit_profile, name='edit-profile'),
    path('staff-requests/', views.view_staff_requests, name='view_staff_requests'),
    path('request-to-work/', views.request_to_work_for_chairman, name='request_to_work'),
    path('approve-staff/<int:staff_id>/', views.approve_staff, name='approve_staff'),
    path('remove-staff/<int:staff_id>/', views.remove_staff, name='remove_staff'),
    path('decline-staff/<int:staff_id>/', views.decline_staff, name='decline_staff'),
    path('reinstate-staff/<int:staff_id>/', views.reinstate_staff, name='reinstate_staff'),
    path('chairman/pending/', views.chairman_pending_posts, name='chairman_pending_posts'),
    path('chairman/post/<int:post_id>/', views.chairman_post_detail, name='chairman_post_detail'),
    path('update_status/<int:post_id>/<str:new_status>/', views.update_staff_post_status, name='update_staff_post_status'),
    path('chairman/archived/', views.chairman_archived_posts, name='chairman_archived_posts'),
    path('reject_staff_post/<int:post_id>/', views.reject_staff_post, name='reject_staff_post'),
    #path('unauthorized/', views.unauthorized, name='unauthorized'),

    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),

    path('staff-profile/', views.staff_profile, name='staff_profile'),
    path('edit-staff-profile/', views.edit_staff_profile, name='edit_staff_profile'),
    path('get_local_government/<int:state_id>/', views.get_local_governments, name='get_local_government'),
    path('get_chairman/<int:local_government_id>/', views.get_chairmen, name='get_chairman'),
    path('create-staff-post/', views.create_staff_post, name='create_staff_post'),
    path('staff/pending/', views.staff_pending_posts, name='staff_pending_posts'),
    path('rejected-posts/', views.rejected_posts_list, name='rejected_posts_list'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),

    path('get-local-governments/<int:state_id>/', views.get_local_governments, name='get_local_governments'),

    path('recent-posts/', views.recent_posts_view, name='recent_posts'),

    #Post comments urls
    path('post/<int:post_id>/', views.post_detail, name='post'),
    path('post/<int:post_id>/add_comment/', views.add_comment, name='add_comment'),
    path('post/<int:comment_id>/add_reply/', views.add_reply, name='add_reply'),
    path('reply/<int:reply_id>/reply_to_reply/', views.add_reply_to_reply, name='reply_to_reply'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('dislike_comment/<int:comment_id>/', views.dislike_comment, name='dislike_comment'),
    path('like_reply/<int:reply_id>/', views.like_reply, name='like_reply'),
    path('dislike_reply/<int:reply_id>/', views.dislike_reply, name='dislike_reply'),
    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('delete_reply/<int:reply_id>/', views.delete_reply, name='delete_reply'),

    path('nested-replies/<int:reply_id>/like/', views.like_nested_reply, name='like_nested_reply'),
    path('nested-replies/<int:reply_id>/dislike/', views.dislike_nested_reply, name='dislike_nested_reply'),
    path('nested-replies/<int:reply_id>/delete/', views.delete_nested_reply, name='delete_nested_reply'),

    # AJAX view for loading comments dynamically
    path('load_comments/<int:post_id>/', views.load_comments, name='load_comments'),

    #staffpost comments urls
    path('staff_post/<int:staffpost_id>/', views.staff_post_detail, name='staff_post_detail'),
    path('add_staff_comment/<int:staffpost_id>/', views.add_staff_comment, name='add_staff_comment'),
    path('add_staff_reply/<int:staffcomment_id>/', views.add_staff_reply, name='add_staff_reply'),
    path('staff_like_comment/<int:staffcomment_id>/', views.staff_like_comment, name='staff_like_comment'),
    path('staff_dislike_comment/<int:staffcomment_id>/', views.staff_dislike_comment, name='staff_dislike_comment'),
    path('staff_like_reply/<int:staffreply_id>/', views.staff_like_reply, name='staff_like_reply'),
    path('staff_dislike_reply/<int:staffreply_id>/', views.staff_dislike_reply, name='staff_dislike_reply'),
    path('staff_delete_comment/<int:staffcomment_id>/', views.staff_delete_comment, name='staff_delete_comment'),
    path('staff_delete_reply/<int:staffreply_id>/', views.staff_delete_reply, name='staff_delete_reply'),

    # AJAX view for loading comments dynamically
    path('load_staff_comments/<int:staffpost_id>/', views.load_staff_comments, name='load_staff_comments'),

    #Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='signin.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

]


websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]