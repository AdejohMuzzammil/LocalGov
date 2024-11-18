from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
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

    states = State.objects.all()
    local_governments = LocalGovernment.objects.all()

    return render(request, 'edit_profile.html', {
        'form': form,
        'states': states,
        'local_governments': local_governments
    })



def get_local_governments(request, state_id):
    local_governments = LocalGovernment.objects.filter(state_id=state_id)
    data = {
        'local_governments': [
            {'id': lga.id, 'name': lga.name} for lga in local_governments
        ]
    }
    return JsonResponse(data)



@login_required
def create_post(request):
    try:
        # Fetch the chairman's profile
        profile = ChairmanProfile.objects.get(user=request.user)

        # Debugging: print the profile details to check what's in the profile
        print(f"Profile: {profile}, State: {profile.state}, Local Government: {profile.local_government}")

        # Check if profile is incomplete (state or local_government are missing)
        if not profile.state or not profile.local_government:
            messages.warning(request, 'You need to complete your profile before creating a post. Please provide all the required details in your profile.')
            return redirect('edit-profile')

        # Check if tenure has ended
        current_date = timezone.now().date()  # Get the current date
        if profile.tenure_end_date and profile.tenure_end_date < current_date:
            messages.warning(request, 'Your tenure has ended. You cannot create posts anymore.')
            return redirect('home')  # Redirect to homepage or another page

    except ChairmanProfile.DoesNotExist:
        messages.warning(request, 'You need to complete your profile before creating a post. Please provide all the required details in your profile.')
        return redirect('edit-profile')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home')  # Redirect after saving the post
    else:
        form = PostForm()

    return render(request, 'create_post.html', {'form': form})


@login_required
def recent_posts_view(request):
    posts = Post.objects.order_by('-created_at')[:5]  
    return render(request, 'recent_posts.html', {'posts': posts})



@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return redirect(f"{reverse('home')}?post_id={post.id}")



@login_required(login_url='/login/')
def add_comment(request, post_id):
    
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Post not found'}, status=404)

    if request.method == "POST":
        text = request.POST.get('text')
        if text:
            comment = Comment.objects.create(post=post, user=request.user, text=text)
            return JsonResponse({
                'status': 'success',
                'comment_id': comment.id,
                'username': comment.user.username,
                'text': comment.text,
                'date': comment.date_commented.strftime("%b %d, %Y")
            })
    return redirect('post_detail', post_id=post_id)


@login_required
def add_reply(request, comment_id, parent_reply_id=None):
    # Retrieve the comment and optional parent reply
    comment = get_object_or_404(Comment, id=comment_id)
    parent_reply = None
    if parent_reply_id:
        parent_reply = get_object_or_404(Reply, id=parent_reply_id)

    # Handle the POST request (creating a new reply)
    if request.method == "POST":
        text = request.POST.get('text')

        # Validate the text
        if text:
            # Create the reply, either as a child of a parent reply or as a direct comment reply
            reply = Reply.objects.create(
                comment=comment,
                parent=parent_reply,
                user=request.user,
                text=text
            )

            # Return JSON response with the reply's data
            return JsonResponse({
                'status': 'success',
                'reply_id': reply.id,
                'username': reply.user.username,
                'text': reply.text,
                'date': reply.date_commented.strftime("%b %d, %Y"),
                'parent_reply_id': parent_reply.id if parent_reply else None,
            })

    return JsonResponse({'status': 'error', 'message': 'Failed to post reply.'})


@login_required
def like_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)

        # Toggle like for the current user
        if request.user in comment.like_count.all():
            comment.like_count.remove(request.user)
        else:
            comment.like_count.add(request.user)
            # Ensure user is not in dislike_count when they like
            comment.dislike_count.remove(request.user)

        comment.save()

        return JsonResponse({
            'status': 'success',
            'like_count': comment.like_count.count(),
            'dislike_count': comment.dislike_count.count()
        })
    except Comment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Comment not found'}, status=404)


@login_required
def dislike_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)

        # Toggle dislike for the current user
        if request.user in comment.dislike_count.all():
            comment.dislike_count.remove(request.user)
        else:
            comment.dislike_count.add(request.user)
            # Ensure user is not in like_count when they dislike
            comment.like_count.remove(request.user)

        comment.save()

        return JsonResponse({
            'status': 'success',
            'like_count': comment.like_count.count(),
            'dislike_count': comment.dislike_count.count()
        })
    except Comment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Comment not found'}, status=404)

@login_required
def like_reply(request, reply_id):
    try:
        reply = Reply.objects.get(id=reply_id)

        # Toggle like for the current user
        if request.user in reply.like_count.all():
            reply.like_count.remove(request.user)
        else:
            reply.like_count.add(request.user)
            # Ensure user is not in dislike_count when they like
            reply.dislike_count.remove(request.user)

        reply.save()

        return JsonResponse({
            'status': 'success',
            'like_count': reply.like_count.count(),
            'dislike_count': reply.dislike_count.count()
        })
    except Reply.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Reply not found'}, status=404)


@login_required
def dislike_reply(request, reply_id):
    try:
        reply = Reply.objects.get(id=reply_id)

        # Toggle dislike for the current user
        if request.user in reply.dislike_count.all():
            reply.dislike_count.remove(request.user)
        else:
            reply.dislike_count.add(request.user)
            # Ensure user is not in like_count when they dislike
            reply.like_count.remove(request.user)

        reply.save()

        return JsonResponse({
            'status': 'success',
            'like_count': reply.like_count.count(),
            'dislike_count': reply.dislike_count.count()
        })
    except Reply.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Reply not found'}, status=404)
    

def delete_comment(request, comment_id):
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.delete()
            return JsonResponse({'status': 'success'})
        except Comment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Comment not found'}, status=404)


@login_required
def delete_reply(request, reply_id):
    reply = Reply.objects.get(id=reply_id)
    if reply.user == request.user:
        reply.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failure', 'message': 'You can only delete your own reply.'})


def load_comments(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = post.comments.all().order_by('-date_commented')
    context = {'comments': comments}
    comments_html = render_to_string('comments_list.html', context)
    return JsonResponse({'status': 'success', 'comments_html': comments_html})