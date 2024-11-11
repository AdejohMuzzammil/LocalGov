from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'),  
    path('post/', views.post, name='post'),
    path('chairman-profile/', views.chairman_profile, name='chairman_profile'),
    path('create-post/', views.create_post, name='create_post'),
    path('edit-profile/', views.edit_profile, name='edit-profile'),
    path('recent-posts/', views.recent_posts_view, name='recent_posts'), 
    #path('posts/', views.post_list, name='post_list'), 
]
