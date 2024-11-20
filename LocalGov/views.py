from django.utils import timezone
from datetime import datetime
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
from django.http import HttpResponseBadRequest
from django.http import Http404
from . models import *
from .forms import *

# Create your views here.

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile_type = form.cleaned_data['profile_type']

            login(request, user)

            # Create UserProfile if not created
            UserProfile.objects.get_or_create(user=user, profile_type=profile_type)

            # Redirect to appropriate profile page
            if profile_type == 'staff':
                return redirect('staff_profile') 

            if profile_type == 'chairman':
                return redirect('chairman_profile')

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

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)

                try:
                    if user.profile_type == 'staff':
                        return redirect('staff_profile')  
                    
                    elif user.profile_type == 'chairman':
                        return redirect('chairman_profile')
                    else:
                        return redirect('home')

                except AttributeError:
                    messages.error(request, "User profile type is missing or not set properly.")
                    return redirect('login')  
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

    return render(request, 'chairman/create_chairman_profile.html', {'form': form})



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
    return render(request, 'chairman/profile.html', {'form': form, 'profile': profile})


@login_required
def edit_profile(request):
    try:
        profile = ChairmanProfile.objects.get(user=request.user)
    except ChairmanProfile.DoesNotExist:
        profile = ChairmanProfile(user=request.user)

    if request.method == 'POST':
        form = ChairmanProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            # Get the selected state and local government from the form
            selected_state_id = form.cleaned_data['state'].id
            selected_local_government_id = form.cleaned_data['local_government'].id

            # Check if any other chairman has selected the same state and local government
            existing_profile = ChairmanProfile.objects.filter(
                state_id=selected_state_id,
                local_government_id=selected_local_government_id
            ).exclude(user=request.user).first()  

            if existing_profile:
                # Check if the tenure of the existing profile has ended
                current_date = datetime.now().date()
                if existing_profile.tenure_end_date >= current_date:
                    # Raise error if the tenure is still active
                    messages.error(request, 'There is an existing chairman from the same State and Local government.')
                    return redirect('edit-profile')  

            # Save the form if all checks pass
            form.save()
            messages.success(request, 'Your Chairman profile has been updated successfully!')
            return redirect('chairman_profile')  

    else:
        form = ChairmanProfileForm(instance=profile)

    states = State.objects.all()
    local_governments = LocalGovernment.objects.all()

    return render(request, 'chairman/edit_profile.html', {
        'form': form,
        'states': states,
        'local_governments': local_governments
    })


@login_required
def chairman_pending_posts(request):
    posts = StaffPost.objects.filter(status='pending')  
    return render(request, 'chairman/chairman_pending_posts.html', {'posts': posts})


@login_required
def chairman_post_detail(request, post_id):
    post = get_object_or_404(StaffPost, id=post_id)

    if request.method == 'POST':
        if 'approve' in request.POST:
            post.status = 'approved'
            post.save()
            return redirect('home')  
        elif 'reject' in request.POST:
            post.status = 'rejected'
            post.save()
            return redirect('chairman_pending_posts')  

    return render(request, 'chairman/chairman_post_detail.html', {'post': post})


@login_required
def chairman_archived_posts(request):
    posts = StaffPost.objects.filter(status='rejected')  
    return render(request, 'chairman/chairman_archived_posts.html', {'posts': posts})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(StaffPost, id=post_id)
    if post.author == request.user or request.user.is_staff:
        post.delete()  # Delete the post
        return redirect('chairman_archived_posts') 
    else:
        return redirect('home') 


@login_required
def request_to_work_for_chairman(request):
    if request.method == 'POST':
        form = StaffRequestForm(request.POST)
        if form.is_valid():
            form.send_request(request.user)
            return redirect('profile_page') 
    else:
        form = StaffRequestForm()

    return render(request, 'staff/staff_profile.html', {'form': form})


@login_required
def view_staff_requests(request):
    chairman_profile = get_object_or_404(ChairmanProfile, user=request.user)
    staff_requests = StaffProfile.objects.filter(desired_chairman=chairman_profile, status='pending')

    # Check if the form was submitted for approval or decline
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        action = request.POST.get('action')
        staff = get_object_or_404(StaffProfile, id=staff_id)

        if action == 'approve':
            staff.status = 'approved'  
            staff.is_approved = True  
        elif action == 'decline':
            staff.status = 'rejected'  
            staff.is_approved = False  

        staff.save()  

        return redirect('view_staff_requests')  

    # Render the page with the list of pending staff requests and the form
    return render(request, 'chairman/staff_requests.html', {
        'staff_requests': staff_requests,  
        'form': StaffApprovalForm(), 
    })


@login_required
def approve_staff(request, staff_id):
    if request.method == 'POST':
        # Get the staff profile by ID
        staff_profile = get_object_or_404(StaffProfile, id=staff_id)

        # Approve the staff profile
        staff_profile.status = 'approved'
        staff_profile.is_approved = True
        staff_profile.save()

        # Fetch all staff profiles (update for rendering)
        staff_requests = StaffProfile.objects.all()

        return render(request, 'chairman/staff_requests.html', {'staff_requests': staff_requests})
    else:
        return HttpResponseBadRequest("Invalid request method.")


@login_required
def decline_staff(request, staff_id):
    chairman_profile = get_object_or_404(ChairmanProfile, user=request.user)
    staff_user = get_object_or_404(User, id=staff_id)
    
    # Remove the staff from the staff requests
    if staff_user in chairman_profile.staff_requests.all():
        chairman_profile.staff_requests.remove(staff_user)

    return redirect('view_staff_requests')


@login_required
def remove_staff(request, staff_id):
    staff = get_object_or_404(StaffProfile, id=staff_id)

    staff.is_approved = False  
    staff.save()

    messages.success(request, 'Staff has been removed from the approved list.')
    return redirect('approved_staff')


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
        profile = ChairmanProfile.objects.get(user=request.user)
        
        # Check if the profile is complete
        if not all([profile.state, profile.local_government, profile.tenure_start_date, profile.tenure_end_date]):
            messages.warning(
                request,
                'You need to complete your profile before creating a post. '
            )
            return redirect('edit-profile')

        # Check if the chairman's tenure has ended
        current_date = timezone.now().date()
        if profile.tenure_end_date < current_date:
            messages.warning(
                request,
                'Your tenure has ended. You cannot create posts anymore.'
            )
            return redirect('chairman_profile') 
    except ChairmanProfile.DoesNotExist:
        messages.warning(
            request,
            'You need to complete your profile before creating a post. '
            'Please provide all the required details in your profile.'
        )
        return redirect('edit-profile')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created successfully.')
            return redirect('home') 
    else:
        form = PostForm(initial={
            'state': profile.state,
            'local_government': profile.local_government
        })

    return render(request, 'chairman/create_post.html', {
        'form': form,
        'state': profile.state,
        'local_government': profile.local_government
    })


@login_required
def recent_posts_view(request):
    posts = Post.objects.order_by('-created_at')[:5]  
    return render(request, 'chairman/recent_posts.html', {'posts': posts})


# Staff Profile View
@login_required
def staff_profile(request):
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    context = {
        'staff': staff,
    
    }
    return render(request, 'staff/staff_profile.html', context)


@login_required
def edit_staff_profile(request):
    staff = get_object_or_404(StaffProfile, user=request.user)

    if request.method == 'POST':
        form = EditStaffProfileForm(request.POST, request.FILES, instance=staff)
        
        if form.is_valid():
            staff_profile = form.save(commit=False)

            # Check if a new profile picture is uploaded
            if 'profile_picture' in request.FILES:
                staff_profile.profile_picture = request.FILES['profile_picture']

            state = staff_profile.state
            local_government = staff_profile.local_government

            # Fetch the ChairmanProfile based on state and local government
            chairman_profile = ChairmanProfile.objects.filter(
                state=state, local_government=local_government
            ).first()

            if chairman_profile:
                staff_profile.desired_chairman = chairman_profile

            # Preserve the approved status if already approved
            if staff_profile.is_approved:
                staff_profile.status = 'approved'  
            else:
                staff_profile.status = 'pending'  
                staff_profile.is_approved = False  

            # Save the updated staff profile
            staff_profile.save()
            messages.success(request, 'Your profile has been successfully updated.')
            return redirect('staff_profile')

        else:
            messages.error(request, 'There was an error in your form. Please check the details and try again.')
    else:
        form = EditStaffProfileForm(instance=staff)

    context = {
        'form': form,
        'staff': staff 
    }
    return render(request, 'staff/edit_staff_profile.html', context)



@login_required
def get_local_governments(request, state_id):
    state = get_object_or_404(State, id=state_id)
    local_governments = LocalGovernment.objects.filter(state=state).values('id', 'name')
    return JsonResponse({'local_governments': list(local_governments)})

@login_required
def get_chairmen(request, local_government_id):
    local_government = get_object_or_404(LocalGovernment, id=local_government_id)
    chairmen = ChairmanProfile.objects.filter(local_government=local_government).values('id', 'user__username')
    return JsonResponse({'chairmen': list(chairmen)})


# Create Staff Post View
@login_required
def create_staff_post(request):
    try:
        # Retrieve the staff profile
        staff_profile = StaffProfile.objects.get(user=request.user)
        chairman = staff_profile.desired_chairman

        # Check if the staff is associated with a chairman
        if not chairman:
            messages.warning(
                request,
                "You are not associated with any chairman. Please contact an administrator."
            )
            return redirect('staff_profile')

        # Check if the staff account is approved by the chairman
        if not staff_profile.is_approved:
            messages.warning(
                request,
                "Your account has not been approved by the chairman. Please contact your chairman for approval."
            )
            return redirect('staff_profile')

        # Check if the chairman's profile is incomplete
        if not all([chairman.state, chairman.local_government, chairman.tenure_start_date, chairman.tenure_end_date]):
            messages.warning(
                request,
                "The chairman you are associated with has not updated their profile. "
                "Please wait until they complete their profile."
            )
            return redirect('staff_profile')

        # Check if the chairman's tenure has ended
        current_date = timezone.now().date()
        if chairman.tenure_end_date and chairman.tenure_end_date < current_date:
            messages.warning(
                request,
                "You cannot create posts because the tenure of the chairman you work for has ended."
            )
            return redirect('staff_profile')

    except StaffProfile.DoesNotExist:
        messages.error(request, "Your staff profile could not be found. Please contact an administrator.")
        return redirect('staff_profile')

    # Handle the post creation
    if request.method == 'POST':
        form = StaffPostForm(request.POST, request.FILES)
        if form.is_valid():
            staff_post = form.save(commit=False)
            staff_post.status = 'pending'  
            staff_post.author = request.user  
            staff_post.save()
            messages.success(request, "Post created successfully and is pending approval.")
            return redirect('staff_profile') 
    else:
        form = StaffPostForm()

    return render(request, 'staff/create_staff_post.html', {
        'form': form,
        'staff_profile': staff_profile
    })


@login_required
def update_staff_post_status(request, post_id, new_status):
    try:
        staff_post = StaffPost.objects.get(id=post_id)
        
        if request.user == staff_post.chairman.user:  
            if new_status in ['approved', 'rejected']:
                staff_post.status = new_status  
                staff_post.save()
                return redirect('staff_profile')  
            else:
                return redirect('staff_profile') 

        else:
            return redirect('staff_profile')

    except StaffPost.DoesNotExist:
        return redirect('staff_profile')


@login_required
def staff_pending_posts(request):
    posts = StaffPost.objects.filter(author=request.user, status='pending') 
    return render(request, 'staff_pending_posts.html', {'posts': posts})
                  

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