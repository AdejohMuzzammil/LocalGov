from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

# Create your models here.

from django.contrib.auth.models import User


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('chairman', 'Chairman'),
        ('staff', 'Staff'),  
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

    # Fields for staff management
    approved_staff = models.ManyToManyField(User, related_name='approved_staff', blank=True)
    staff_requests = models.ManyToManyField(User, related_name='staff_requests', blank=True)

    def __str__(self):
        return self.user.username

    
class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='staff_profile_pictures/', blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    local_government = models.ForeignKey(LocalGovernment, on_delete=models.SET_NULL, null=True, blank=True)
    desired_chairman = models.ForeignKey(ChairmanProfile, on_delete=models.SET_NULL, null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('removed', 'Removed'),  
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
class StaffPost(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='media/post_images/', blank=True, null=True)
    video = models.FileField(upload_to='media/post_videos/', blank=True, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)

    # Related fields
    state = models.ForeignKey(State, related_name='staffpost_states', on_delete=models.CASCADE)
    local_government = models.ForeignKey(LocalGovernment, related_name='staffpost_local_governments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='staffpost_author', on_delete=models.CASCADE)
    chairman = models.ForeignKey(ChairmanProfile, related_name='staffpost_chairman', on_delete=models.CASCADE)

    # Location fields
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Post status and feedback
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, null=True) 

    def __str__(self):
        return self.title
   
     
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

    class Meta:
        verbose_name = "Reply"
        verbose_name_plural = "Replies"

    def __str__(self):
        return f'Reply by {self.user.username} on {self.comment.text}'    

class ReplyToReply(models.Model):
    reply = models.ForeignKey(Reply, related_name='nested_replies', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='child_replies', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)
    like_count = models.ManyToManyField(User, related_name='liked_reply_to_replies', blank=True)
    dislike_count = models.ManyToManyField(User, related_name='disliked_reply_to_replies', blank=True)

    class Meta:
        verbose_name = "Reply to Reply"
        verbose_name_plural = "Replies to Replies"

    def __str__(self):
        return f'Reply to Reply by {self.user.username} on reply: "{self.reply.text[:30]}"'


class StaffPostComment(models.Model):
    staff_post = models.ForeignKey(StaffPost, related_name='staff_comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)
    like_count = models.ManyToManyField(User, related_name='liked_staff_comments', blank=True)
    dislike_count = models.ManyToManyField(User, related_name='disliked_staff_comments', blank=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.staff_post.title}'

class StaffPostReply(models.Model):
    comment = models.ForeignKey(StaffPostComment, related_name='staff_replies', on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', related_name='child_replies', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)
    like_count = models.ManyToManyField(User, related_name='liked_staff_replies', blank=True)
    dislike_count = models.ManyToManyField(User, related_name='disliked_staff_replies', blank=True)

    class Meta:
        verbose_name = "Staff Post Reply"
        verbose_name_plural = "Staff Post Replies"

    def __str__(self):
        return f'Reply by {self.user.username} on {self.comment.text}'


class StaffPostNestedReply(models.Model):
    reply = models.ForeignKey(StaffPostReply, related_name='nested_replies', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='child_nested_replies', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_commented = models.DateTimeField(auto_now_add=True)
    like_count = models.ManyToManyField(User, related_name='liked_staff_nested_replies', blank=True)
    dislike_count = models.ManyToManyField(User, related_name='disliked_staff_nested_replies', blank=True)

    class Meta:
        verbose_name = "Staff Nested Reply"
        verbose_name_plural = "Staff Nested Replies"

    def __str__(self):
        return f'Nested Reply by {self.user.username} on reply: "{self.reply.text[:30]}"'


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, default="Default Plan")
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount}"
    

class Subscription(models.Model):
    chairman = models.OneToOneField('ChairmanProfile', on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    payment_date = models.DateField(blank=True, null=True)
    next_payment_due = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.chairman.user.username} Subscription"
