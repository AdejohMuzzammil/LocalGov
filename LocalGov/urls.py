from django.urls import path
from . import views 
from django.urls import re_path
from .consumers import NotificationConsumer


urlpatterns = [
    path('', views.home, name='home'), 
    path('create-post/', views.create_post, name='create_post'),
    path('chairman-profile/', views.chairman_profile, name='chairman_profile'),
    path('edit-profile/', views.edit_profile, name='edit-profile'),
    path('recent-posts/', views.recent_posts_view, name='recent_posts'),
    #path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/add-comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('like-comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('dislike-comment/<int:comment_id>/', views.dislike_comment, name='dislike_comment'),
]


websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]