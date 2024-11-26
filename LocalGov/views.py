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

import logging
logger = logging.getLogger(__name__)

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
    approved_posts = StaffPost.objects.filter(status='approved')
    return render(request, 'home.html', 
                  {'posts': posts, 'approved_posts': approved_posts})


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
        # Retrieve the chairman's profile or create a new one if not found
        profile = ChairmanProfile.objects.get(user=request.user)
    except ChairmanProfile.DoesNotExist:
        profile = ChairmanProfile(user=request.user)

    if request.method == 'POST':
        # Handle profile update
        form = ChairmanProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Chairman profile has been updated successfully!')
            return redirect('chairman_profile')
    else:
        form = ChairmanProfileForm(instance=profile)

    # Fetch pending posts (from StaffPost) and staff requests (from StaffProfile)
    pending_posts = StaffPost.objects.filter(chairman=profile, status='pending')
    pending_requests = StaffProfile.objects.filter(desired_chairman=profile, status='pending')

    # Count the total pending notifications
    total_pending_notifications = pending_posts.count() + pending_requests.count()

    # Handle AJAX request for updating the notification counter
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'total_pending_notifications': total_pending_notifications})

    # Render the template for normal requests
    return render(request, 'chairman/profile.html', {
        'form': form,
        'profile': profile,
        'pending_posts': pending_posts,
        'pending_requests': pending_requests,
        'total_pending_notifications': total_pending_notifications,
    })


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
    try:
        chairman_profile = ChairmanProfile.objects.get(user=request.user)

        posts = StaffPost.objects.filter(chairman=chairman_profile, status='pending')

        if request.method == 'POST':
            post_id = request.POST.get('post_id')
            action = request.POST.get('action')
            post = get_object_or_404(StaffPost, id=post_id)

            if action == 'approve':
                # Approve the post
                post.status = 'approved'
                post.save()

                # Show success message
                messages.success(request, f"Post '{post.title}' approved.")

                # Redirect to the home page
                return redirect('home')  

            elif action == 'reject':
                # Reject the post
                post.status = 'rejected'
                post.save()

                # Show success message
                messages.success(request, f"Post '{post.title}' rejected.")

                # Redirect to the chairman_pending_posts page
                return redirect('chairman_pending_posts')

    except ChairmanProfile.DoesNotExist:
        messages.error(request, "You are not authorized to approve or reject posts.")
        return redirect('unauthorized')

    return render(request, 'chairman/chairman_pending_posts.html', {
        'posts': posts,
    })


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

    # Fetch staff requests with different statuses
    pending_staff_requests = StaffProfile.objects.filter(desired_chairman=chairman_profile, status='pending')
    approved_staff = StaffProfile.objects.filter(desired_chairman=chairman_profile, status='approved')
    declined_staff = StaffProfile.objects.filter(desired_chairman=chairman_profile, status='declined')
    removed_staff = StaffProfile.objects.filter(desired_chairman=chairman_profile, status='removed')

    # Check if it's an AJAX request for fetching pending count
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
        staff_request_count = pending_staff_requests.count()
        return JsonResponse({'staff_request_count': staff_request_count})

    # Handle form submissions for approval, decline, removal, or reinstatement
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        action = request.POST.get('action')

        # Ensure the staff is associated with this chairman
        staff = get_object_or_404(StaffProfile, id=staff_id, desired_chairman=chairman_profile)

        # Perform the appropriate action
        if action == 'approve':
            staff.status = 'approved'
            staff.is_approved = True
            chairman_profile.staff_requests.remove(staff.user)  # Remove from requests
            chairman_profile.approved_staff.add(staff.user)  # Add to approved staff
        elif action == 'decline':
            staff.status = 'declined'
            staff.is_approved = False
            chairman_profile.staff_requests.remove(staff.user)  # Remove from requests
        elif action == 'remove':
            staff.status = 'removed'
            chairman_profile.approved_staff.remove(staff.user)  # Remove from approved staff
        elif action == 'reinstate':
            staff.status = 'pending'
            chairman_profile.staff_requests.add(staff.user)  # Add back to requests

        staff.save()
        return redirect('view_staff_requests')

    # Fetch the count of pending requests
    staff_request_count = pending_staff_requests.count()

    return render(request, 'chairman/staff_requests.html', {
        'pending_staff_requests': pending_staff_requests,
        'approved_staff': approved_staff,
        'declined_staff': declined_staff,
        'removed_staff': removed_staff,
        'staff_request_count': staff_request_count,
    })
  

@login_required
def approve_staff(request, staff_id):
    if request.method == 'POST':
        # Get the staff profile by ID
        staff = get_object_or_404(StaffProfile, id=staff_id)

        # Approve the staff profile
        staff.status = 'approved'
        staff.is_approved = True
        staff.save()

        # Display a success message
        messages.success(request, f'{staff.user.first_name} {staff.user.last_name} has been approved.')

        # Fetch the updated list of approved staff
        approved_staff = StaffProfile.objects.filter(is_approved=True)

        # Render the updated list back to the same page
        return render(request, 'chairman/staff_requests.html', {'staff_requests': approved_staff})

    # If not a POST request, redirect to the list view
    return redirect('view_staff_requests')


@login_required
def decline_staff(request, staff_id):
    try:
        if request.method == 'POST':
            # Get the chairman's profile
            chairman_profile = get_object_or_404(ChairmanProfile, user=request.user)
            
            # Get the staff's profile
            staff = get_object_or_404(StaffProfile, id=staff_id)
            staff_user = staff.user  # Correct reference to the User instance
            
            # Check if the staff's user is in the chairman's staff_requests
            if chairman_profile.staff_requests.filter(id=staff_user.id).exists():
                # Remove the staff's user from staff_requests
                chairman_profile.staff_requests.remove(staff_user)
                chairman_profile.save()

                # Update the staff profile's status to "declined"
                staff.status = 'declined'
                staff.save()

                # Provide feedback to the user
                messages.success(
                    request, 
                    f"{staff_user.first_name} {staff_user.last_name}'s request has been declined."
                )
            else:
                # Log the situation if staff isn't found in the chairman's requests
                messages.error(request, 'This staff member is not in your staff requests.')
                print(f"Staff ID: {staff.id} not found in chairman's staff requests.")
    
    except StaffProfile.DoesNotExist:
        messages.error(request, 'The staff member does not exist.')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        print(f"Error in decline_staff view: {e}") 
    
    return redirect('view_staff_requests')


@login_required
def remove_staff(request, staff_id):
    print(f"Received staff_id for removal: {staff_id}")  # Debugging line

    try:
        # Get the staff profile based on staff_id
        staff = StaffProfile.objects.get(id=staff_id)

        # Change the staff's status and approval status
        staff.status = 'removed'
        staff.is_approved = False
        staff.save()

        # Success message
        messages.success(request, f'{staff.user.first_name} {staff.user.last_name} has been removed from the approved list.')

    except StaffProfile.DoesNotExist:
        # Error message
        messages.error(request, 'Staff profile not found.')

    # Redirect to the list of staff requests
    return redirect('view_staff_requests')


@login_required
def reinstate_staff(request, staff_id):
    staff = get_object_or_404(StaffProfile, id=staff_id)
    try:
        chairman_profile = ChairmanProfile.objects.get(user=request.user)
    except ChairmanProfile.DoesNotExist:
        return redirect('unauthorized')

    staff.status = 'approved'
    staff.is_approved = True
    staff.save()
    messages.success(request, f'{staff.user.first_name} {staff.user.last_name} has been reinstated.')
    return redirect('view_staff_requests')


@login_required
def reject_staff_post(request, post_id):
    if request.method == 'POST':
        feedback = request.POST.get('feedback')

        # Fetch the post or return a 404 error if not found
        post = get_object_or_404(StaffPost, id=post_id)
        
        # Process rejection logic
        post.status = 'rejected'  
        post.feedback = feedback  
        post.save()

        
        return redirect('chairman_pending_posts')
    return redirect('chairman_pending_posts')



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

    # Check the staff profile's status
    if staff.status == 'approved':
        messages.info(request, 'Your profile has been approved and cannot be edited.')
        return redirect('staff_profile')

    if staff.status == 'removed':
        messages.error(request, 'Your profile has been removed and cannot be edited.')
        return redirect('staff_profile')

    if staff.status not in ['pending', 'declined']:
        messages.error(request, 'You cannot edit your profile at this moment.')
        return redirect('staff_profile')

    if request.method == 'POST':
        form = EditStaffProfileForm(request.POST, request.FILES, instance=staff)
        
        if form.is_valid():
            staff_profile = form.save(commit=False)

            # Update profile picture if provided
            if 'profile_picture' in request.FILES:
                staff_profile.profile_picture = request.FILES['profile_picture']

            state = staff_profile.state
            local_government = staff_profile.local_government

            # Fetch the new chairman profile
            new_chairman = ChairmanProfile.objects.filter(
                state=state, local_government=local_government
            ).first()

            # Remove staff from previous chairman's requests
            if staff_profile.desired_chairman and staff_profile.desired_chairman != new_chairman:
                staff_profile.desired_chairman.staff_requests.remove(staff_profile.user)

            # Update the desired chairman
            staff_profile.desired_chairman = new_chairman

            # Add staff to the new chairman's requests if status is 'pending'
            if new_chairman and staff_profile.status == 'pending':
                if not new_chairman.staff_requests.filter(id=staff_profile.user.id).exists():
                    new_chairman.staff_requests.add(staff_profile.user)

            # Update staff status
            if staff_profile.is_approved:
                staff_profile.status = 'approved'
            else:
                staff_profile.status = 'pending'
                staff_profile.is_approved = False

            # Save changes
            staff_profile.save()
            messages.success(
                request,
                'Your profile has been successfully updated. A request was sent to the chairman for approval.'
            )
            return redirect('staff_profile')

        else:
            messages.error(request, 'There was an error in your form. Please check the details and try again.')
    else:
        form = EditStaffProfileForm(instance=staff)

    context = {
        'form': form,
        'staff': staff,
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


@login_required
def create_staff_post(request):
    try:
        # Retrieve the staff profile
        staff_profile = StaffProfile.objects.get(user=request.user)

        # Check if the staff profile status is 'removed' or 'declined'
        if staff_profile.status == 'removed':
            messages.error(request, "Your profile has been removed by the chairman. You cannot create a post.")
            return redirect('staff_profile')

        if staff_profile.status == 'declined':
            chairman_name = staff_profile.desired_chairman.name if staff_profile.desired_chairman else "Unknown Chairman"
            messages.error(request, f"Your profile was declined by {chairman_name}. You cannot create a post.")
            return redirect('staff_profile')

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
            staff_post.chairman = staff_profile.desired_chairman  
            staff_post.save() 
            messages.success(request, "Post created successfully and is pending approval.")
            return redirect('staff_profile')  
        else:
            messages.error(request, "There was an error creating the post. Please check the form for errors.")
    else:
        form = StaffPostForm()

    return render(request, 'staff/create_staff_post.html', {
        'form': form,
        'staff_profile': staff_profile
    })


@login_required
def rejected_posts_list(request):
    rejected_posts = StaffPost.objects.filter(author=request.user, status='rejected')
    rejected_count = rejected_posts.count()

    # Render the HTML for the list of rejected posts
    rejected_posts_html = render_to_string('staff/rejected_posts_list.html', {'rejected_posts': rejected_posts})

    # Return JSON with the count and HTML for dynamic update
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'rejected_count': rejected_count,
            'rejected_posts_html': rejected_posts_html
        })

    # For non-AJAX requests, render the full page
    return render(request, 'staff/rejected_posts_list.html', {
        'rejected_posts': rejected_posts,
        'rejected_count': rejected_count,
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(StaffPost, id=post_id, author=request.user)

    if request.method == 'POST':
        form = StaffPostEditForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post.status = 'pending' 
            post.save()  
            form.save()  
            messages.success(request, 'Your post has been updated and is now pending approval.')
            return redirect('rejected_posts_list')
        else:
            print(form.errors)  
    else:
        form = StaffPostEditForm(instance=post)
    return render(request, 'staff/edit_post.html', {'form': form, 'post': post})


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


@login_required
def load_comments(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = post.comments.all().order_by('-date_commented')
    context = {'comments': comments}
    comments_html = render_to_string('comments_list.html', context)
    return JsonResponse({'status': 'success', 'comments_html': comments_html})



# View for displaying staff post detail
@login_required
def staff_post_detail(request, staffpost_id):
    staff_post = get_object_or_404(StaffPost, id=staffpost_id)
    # Redirecting to home with the staffpost_id as a query parameter
    return redirect(f"{reverse('home')}?staffpost_id={staff_post.id}")

# View for adding a comment to a staff post
@login_required
def add_staff_comment(request, staffpost_id):
    staff_post = get_object_or_404(StaffPost, id=staffpost_id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text', '').strip()
        if not comment_text:
            return JsonResponse({'success': False, 'message': 'Comment cannot be empty.'})

        # Save the comment
        comment = StaffPostComment.objects.create(
            staff_post=staff_post,
            user=request.user,
            text=comment_text
        )

        # Return data to render the new comment
        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'username': comment.user.username,
            'text': comment.text,
            'date': comment.date_commented.strftime("%b %d, %Y"),
            'message': 'You commented on this post.'
        })
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



# View for adding a reply to a comment
@login_required
def add_staff_reply(request, staffcomment_id, parent_reply_id=None):
    comment = get_object_or_404(StaffPostComment, id=staffcomment_id)
    parent_reply = None
    if parent_reply_id:
        parent_reply = get_object_or_404(StaffPostReply, id=parent_reply_id)

    if request.method == "POST":
        text = request.POST.get('text')
        if text:
            # Create the reply object and save it
            reply = StaffPostReply.objects.create(
                comment=comment,
                parent=parent_reply,
                user=request.user,
                text=text
            )
            
            # Return a JSON response with the newly created reply data
            return JsonResponse({
                'status': 'success',
                'reply_id': reply.id,
                'username': reply.user.username,
                'text': reply.text,
                'date': reply.date_commented.strftime("%b %d, %Y"),
                'parent_reply_id': parent_reply.id if parent_reply else None,
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Reply text cannot be empty.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

# View for liking a comment
@login_required
def staff_like_comment(request, staffcomment_id):
    comment = get_object_or_404(StaffPostComment, id=staffcomment_id)
    user = request.user
    if user not in comment.like_count.all():
        comment.like_count.add(user)
    else:
        comment.like_count.remove(user)
    return redirect('staff_post_detail', staffpost_id=comment.staff_post.id)

# View for disliking a comment
@login_required
def staff_dislike_comment(request, staffcomment_id):
    comment = get_object_or_404(StaffPostComment, id=staffcomment_id)
    user = request.user
    if user not in comment.dislike_count.all():
        comment.dislike_count.add(user)
    else:
        comment.dislike_count.remove(user)
    return redirect('staff_post_detail', staffpost_id=comment.staff_post.id)

# View for liking a reply
@login_required
def staff_like_reply(request, staffreply_id):
    reply = get_object_or_404(StaffPostReply, id=staffreply_id)
    user = request.user
    if user not in reply.like_count.all():
        reply.like_count.add(user)
    else:
        reply.like_count.remove(user)
    return redirect('staff_post_detail', staffpost_id=reply.comment.staff_post.id)

# View for disliking a reply
@login_required
def staff_dislike_reply(request, staffreply_id):
    reply = get_object_or_404(StaffPostReply, id=staffreply_id)
    user = request.user
    if user not in reply.dislike_count.all():
        reply.dislike_count.add(user)
    else:
        reply.dislike_count.remove(user)
    return redirect('staff_post_detail', staffpost_id=reply.comment.staff_post.id)

# View for deleting a comment
@login_required
def staff_delete_comment(request, staffcomment_id):
    comment = get_object_or_404(StaffPostComment, id=staffcomment_id)
    if comment.user == request.user or request.user.is_staff:
        comment.delete()
    return redirect('staff_post_detail', staffpost_id=comment.staff_post.id)

# View for deleting a reply
@login_required
def staff_delete_reply(request, staffreply_id):
    reply = get_object_or_404(StaffPostReply, id=staffreply_id)
    if reply.user == request.user or request.user.is_staff:
        reply.delete()
    return redirect('staff_post_detail', staffpost_id=reply.comment.staff_post.id)


# AJAX view for loading staff comments dynamically
@login_required
def load_staff_comments(request, staffpost_id):
    try:
        staff_post = StaffPost.objects.get(id=staffpost_id)
    except StaffPost.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Post not found'}, status=404)

    comments = staff_post.staff_comments.all().order_by('-date_commented')
    context = {'comments': comments}
    comments_html = render_to_string('comments_list.html', context)

    return JsonResponse({'status': 'success', 'comments_html': comments_html})