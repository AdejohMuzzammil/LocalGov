from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

from django.contrib.auth.models import User


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('chairman', 'Chairman'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=20)

    def __str__(self):
        return self.user.username

class State(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class LocalGovernment(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, related_name='local_governments', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ChairmanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    # Updated related_name attributes to avoid clashes
    state = models.ForeignKey(
        State, 
        related_name='chairman_profiles', 
        on_delete=models.CASCADE,
        null=True,  
        blank=True  
    )
    local_government = models.ForeignKey(
        LocalGovernment, 
        related_name='chairman_profiles', 
        on_delete=models.SET_NULL,  
        null=True, 
        blank=True  
    )
    tenure_start_date = models.DateField(blank=True, null=True)
    tenure_end_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField()

    def __str__(self):
        return self.user.username

    
class Post(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='media/post_images/', blank=True, null=True)
    video = models.FileField(upload_to='media/post_videos/', blank=True, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey(State, related_name='post_states', on_delete=models.CASCADE)
    local_government = models.ForeignKey(LocalGovernment, related_name='post_local_governments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    def __str__(self):
        return self.title

    

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)
    like_count = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    dislike_count = models.ManyToManyField(User, related_name='disliked_comments', blank=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'


class Reply(models.Model):
    comment = models.ForeignKey(Comment, related_name='replies', on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', related_name='child_replies', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)
    like_count = models.ManyToManyField(User, related_name='liked_replies', blank=True)
    dislike_count = models.ManyToManyField(User, related_name='disliked_replies', blank=True)

    def __str__(self):
        return f'Reply by {self.user.username} on {self.comment.text}'


