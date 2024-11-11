from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from . models import *
from . forms import *

# Create your views here.

def home(request):
    return render(request, 'home.html')


def chairman_profile(request):
    profile = ChairmanProfile.objects.get(user=request.user)
    return render(request, 'profile.html', {'profile': profile})


@login_required
def edit_profile(request):
    profile = get_object_or_404(ChairmanProfile, user=request.user)

    if request.method == 'POST':
        form = ChairmanProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('edit-profile')  
    else:
        form = ChairmanProfileForm(instance=profile)

    return render(request, 'edit_profile.html',
                   {'form': form})


def create_post(request):
    # Logic for creating a post
    return render(request, 'create_post.html')

def post(request):
    posts = Post.objects.all() 
    print(Post.objects.all()) 
    return render(request, 'home.html', {'posts': posts})


def recent_posts_view(request):
    posts = Post.objects.order_by('-created_at')[:5]  
    return render(request, 'recent_posts.html', {'posts': posts})
