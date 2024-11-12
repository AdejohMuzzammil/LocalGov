from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate,login
from . models import *
from .forms import *

# Create your views here.


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the user and associated profile
            user = form.save()
            profile_type = form.cleaned_data['profile_type']

            # Log the user in
            login(request, user)

            # Create ChairmanProfile if the profile type is 'chairman'
            if profile_type == 'chairman':
                return redirect('create_chairman_profile')
            else:
                return redirect('home')
        else:
            print(form.errors)  
    else:
        form = CustomUserCreationForm()

    return render(request, 'signup.html', {'form': form})


# Login view (modifying as needed)
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Authenticate the user
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                # Redirect based on the user's profile type
                if user.profile_type == 'CHAIRMAN':
                    return redirect('chairman_profile')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid login credentials.")
        else:
            messages.error(request, "Form is invalid.")
    else:
        form = LoginForm()

    return render(request, 'signin.html', {'form': form})



def home(request):
    posts = Post.objects.all()  
    return render(request, 'home.html', {'posts': posts})


@login_required
def create_chairman_profile(request):
    if request.method == 'POST':
        form = ChairmanProfileForm(request.POST, request.FILES)
        if form.is_valid():
            chairman_profile = form.save(commit=False)
            chairman_profile.user = request.user  # Link the profile to the logged-in user
            chairman_profile.save()
            messages.success(request, 'Your Chairman profile has been created successfully!')
            return redirect('chairman_profile')
    else:
        form = ChairmanProfileForm()

    return render(request, 'create_chairman_profile.html', {'form': form})



@login_required
def chairman_profile(request):
    try:
        profile = ChairmanProfile.objects.get(user=request.user)
    except ChairmanProfile.DoesNotExist:
        profile = ChairmanProfile(user=request.user)
        profile.save()  

    if request.method == 'POST':
        form = ChairmanProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()  
            return redirect('chairman_profile')  
    else:
        form = ChairmanProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form, 'profile': profile})


# Edit Chairman Profile (view for updating the profile details)
@login_required
def edit_profile(request):
    try:
        profile = ChairmanProfile.objects.get(user=request.user)
    except ChairmanProfile.DoesNotExist:
        profile = ChairmanProfile(user=request.user)

    if request.method == 'POST':
        form = ChairmanProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Chairman profile has been updated successfully!')
            return redirect('chairman_profile')  
    else:
        form = ChairmanProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})


@login_required
def create_post(request):
    try:
        profile = ChairmanProfile.objects.get(user=request.user)
    except ChairmanProfile.DoesNotExist:
        messages.warning(request, 
                         'You need to complete your profile before creating a post. Please provide all the required details in your profile.')
        return redirect('edit-profile')  

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home') 
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})


@login_required
def recent_posts_view(request):
    posts = Post.objects.order_by('-created_at')[:5]  
    return render(request, 'recent_posts.html', {'posts': posts})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to comment.")
        return redirect('login')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            comment = Comment.objects.create(post=post, user=request.user, text=text)
            messages.success(request, 'Your comment has been posted successfully!')
            return redirect('home')  

    return redirect('home')


@login_required
def reply_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    parent_comment = get_object_or_404(Comment, id=comment_id)

    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to reply.")
        return redirect('login')

    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            reply = Comment.objects.create(post=post, user=request.user, text=text, parent_comment=parent_comment)
            messages.success(request, 'Your reply has been posted successfully!')

            # Send live notification to the original comment's owner
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{parent_comment.user.id}',  # Unique channel name for the user
                {
                    'type': 'comment.notification',
                    'message': f'Your comment has a new reply from {request.user.username}!',
                }
            )

            return redirect('home')
    return redirect('home')


@login_required
@require_POST
def like_comment(request, comment_id):
    try:
        # Retrieve the comment
        comment = Comment.objects.get(id=comment_id)

        # Process like/unlike logic
        if request.user in comment.like_count.all():
            comment.like_count.remove(request.user)
            status = 'removed'
        else:
            comment.like_count.add(request.user)
            status = 'added'

        comment.save()

        # Send live notification to the comment's owner
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{comment.user.id}',  # Unique channel name for the user
            {
                'type': 'comment.notification',
                'message': f'Your comment was {status} by {request.user.username}!',
            }
        )

        return JsonResponse({'status': status})
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)


@login_required
@require_POST
def dislike_comment(request, comment_id):
    try:
        # Retrieve the comment
        comment = Comment.objects.get(id=comment_id)

        # Process dislike/undislike logic
        if request.user in comment.dislike_count.all():
            comment.dislike_count.remove(request.user)
            status = 'removed'
        else:
            comment.dislike_count.add(request.user)
            status = 'added'

        comment.save()

        # Send live notification to the comment's owner
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{comment.user.id}',  # Unique channel name for the user
            {
                'type': 'comment.notification',
                'message': f'Your comment was {status} by {request.user.username}!',
            }
        )

        return JsonResponse({'status': status})
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)