from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
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
                return redirect('chairman_profile')
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

    if request.method == 'POST':
        form = ChairmanProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()  
            messages.success(request, 'Your Chairman profile has been updated successfully!')
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

        if not profile.state or not profile.local_government:
            messages.warning(request, 'You need to complete your profile before creating a post. Please provide all the required details in your profile.')
            return redirect('edit-profile')  
    except ChairmanProfile.DoesNotExist:
        messages.warning(request, 'You need to complete your profile before creating a post. Please provide all the required details in your profile.')
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

    messages.error(request, "Failed to add your comment. Please try again.")
    return redirect('home')


@login_required
def reply_comment(request, post_id, comment_id, reply_id=None):
    # Debugging: Print incoming IDs
    print(f"Received post_id: {post_id}, comment_id: {comment_id}, reply_id: {reply_id}")

    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)  # Check if the comment belongs to the post

    parent_reply = None
    if reply_id:
        parent_reply = get_object_or_404(Reply, id=reply_id)

    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            reply = Reply.objects.create(
                comment=comment,
                parent=parent_reply,
                user=request.user,
                text=text
            )
            messages.success(request, 'Your reply has been posted successfully!')

            recipient = parent_reply.user if parent_reply else comment.user
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{recipient.id}',
                {
                    'type': 'comment.notification',
                    'message': f'Your {"reply" if parent_reply else "comment"} has a new reply from {request.user.username}!',
                }
            )
            return redirect('home')

    messages.error(request, "Failed to add your reply. Please try again.")
    return redirect('home')


@login_required
@require_POST
def like_comment(request, comment_id):
    try:
        # Retrieve the comment
        comment = Comment.objects.get(id=comment_id)
        user = request.user

        # Handle like logic
        if user in comment.like_count.all():
            comment.like_count.remove(user)
            status = 'removed'
        else:
            comment.like_count.add(user)
            status = 'added'
            # If the user had previously disliked the comment, remove the dislike
            if user in comment.dislike_count.all():
                comment.dislike_count.remove(user)

        comment.save()

        # Send live notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{comment.user.id}',
            {'type': 'comment.notification', 'message': f'Your comment was {status} by {user.username}!'}
        )

        return JsonResponse({
            'status': status,
            'like_count': comment.like_count.count(),
            'dislike_count': comment.dislike_count.count()
        })
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)
    

@login_required
@require_POST
def dislike_comment(request, comment_id):
    try:
        # Retrieve the comment
        comment = Comment.objects.get(id=comment_id)
        user = request.user

        # Handle dislike logic
        if user in comment.dislike_count.all():
            comment.dislike_count.remove(user)
            status = 'removed'
        else:
            comment.dislike_count.add(user)
            status = 'added'
            if user in comment.like_count.all():
                comment.like_count.remove(user)

        comment.save()

        # Send live notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{comment.user.id}', 
            {'type': 'comment.notification', 'message': f'Your comment was {status} by {user.username}!'}
        )

        return JsonResponse({
            'status': status,
            'like_count': comment.like_count.count(),
            'dislike_count': comment.dislike_count.count()
        })
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)
    


@login_required
@require_POST
def like_reply(request, reply_id):
    try:
        reply = Reply.objects.get(id=reply_id)
        user = request.user

        # Handle liking logic
        if user in reply.like_count.all():
            reply.like_count.remove(user)
            status = 'removed'
        else:
            reply.like_count.add(user)
            status = 'added'
            if user in reply.dislike_count.all():
                reply.dislike_count.remove(user)

        reply.save()

        # Send real-time notification
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{reply.user.id}',
                {
                    'type': 'comment.notification',
                    'message': f'Your reply was {status} by {user.username}!',
                }
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")

        return JsonResponse({
            'status': status,
            'like_count': reply.like_count.count(),
            'dislike_count': reply.dislike_count.count()
        })

    except Reply.DoesNotExist:
        return JsonResponse({'error': 'Reply not found'}, status=404)
    except Exception as e:
        print(f"Error in like_reply view: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    

@login_required
@require_POST
def dislike_reply(request, reply_id):
    try:
        reply = Reply.objects.get(id=reply_id)
        user = request.user

        # Handle disliking logic
        if user in reply.dislike_count.all():
            reply.dislike_count.remove(user)
            status = 'removed'
        else:
            reply.dislike_count.add(user)
            status = 'added'
            if user in reply.like_count.all():
                reply.like_count.remove(user)

        reply.save()

        # Send real-time notification
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{reply.user.id}',
                {
                    'type': 'comment.notification',
                    'message': f'Your reply was {status} by {user.username}!',
                }
            )
        except Exception as e:
            print(f"WebSocket notification error: {e}")

        return JsonResponse({
            'status': status,
            'like_count': reply.like_count.count(),
            'dislike_count': reply.dislike_count.count()
        })

    except Reply.DoesNotExist:
        return JsonResponse({'error': 'Reply not found'}, status=404)
    except Exception as e:
        print(f"Error in dislike_reply view: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)