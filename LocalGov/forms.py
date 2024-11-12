from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from . models import *


class CustomUserCreationForm(UserCreationForm):
    profile_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="Profile Type"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'profile_type']

    def save(self, commit=True):
        user = super().save(commit=False)
        profile_type = self.cleaned_data['profile_type']
        
        if commit:
            user.save()
            # Create or update UserProfile instance
            user_profile = UserProfile.objects.create(user=user, profile_type=profile_type)
            
            # Create ChairmanProfile if the user is a chairman
            if profile_type == 'chairman':
                ChairmanProfile.objects.create(user=user)  # Ensure this creates the profile for the chairman
            
        return user
    

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

class ChairmanProfileForm(forms.ModelForm):
    class Meta:
        model = ChairmanProfile
        fields = [
            'profile_picture', 'bio', 'state', 'local_government',
            'phone_number', 'email', 'tenure_start_date', 'tenure_end_date'
        ]
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'local_government': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tenure_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tenure_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title',
            'description',
            'image',
            'video',
            'state',
            'local_government',
            'location',
            'latitude',
            'longitude'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your post content'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'video': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'local_government': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the location'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text'] 

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({'placeholder': 'Reply to this comment', 'class': 'form-control'})
