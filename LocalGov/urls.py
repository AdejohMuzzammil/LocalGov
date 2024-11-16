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
    path('recent-posts/', views.recent_posts_view, name='recent_posts'),

    path('post/<int:post_id>/', views.post_detail, name='post'),

    path('post/<int:post_id>/add_comment/', views.add_comment, name='add_comment'),
    path('add_reply/<int:comment_id>/', views.add_reply, name='add_reply'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('dislike_comment/<int:comment_id>/', views.dislike_comment, name='dislike_comment'),
    path('like_reply/<int:reply_id>/', views.like_reply, name='like_reply'),
    path('dislike_reply/<int:reply_id>/', views.dislike_reply, name='dislike_reply'),

    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('delete_reply/<int:reply_id>/', views.delete_reply, name='delete_reply'),
    path('load_comments/<int:post_id>/', views.load_comments, name='load_comments'),

    #Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='signin.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

]


websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]