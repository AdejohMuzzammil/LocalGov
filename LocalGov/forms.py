from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
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
            try:
                user.save()
                if not UserProfile.objects.filter(user=user).exists():
                    user_profile = UserProfile.objects.create(user=user, profile_type=profile_type)

                # Only create StaffProfile with user for staff users
                if profile_type == 'staff' and not StaffProfile.objects.filter(user=user).exists():
                    StaffProfile.objects.create(user=user)

                if profile_type == 'chairman' and not ChairmanProfile.objects.filter(user=user).exists():
                    ChairmanProfile.objects.create(user=user)

            except IntegrityError as e:
                user.delete()  
                raise IntegrityError(f"Error creating profiles: {e}")

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Disable the tenure fields if the tenure start and end dates are already set
        if self.instance.tenure_start_date and self.instance.tenure_end_date:
            self.fields['tenure_start_date'].disabled = True
            self.fields['tenure_end_date'].disabled = True

class StaffRequestForm(forms.Form):
    chairman_id = forms.IntegerField()

    def send_request(self, user):
        chairman = get_object_or_404(ChairmanProfile, id=self.cleaned_data['chairman_id'])
        chairman.staff_requests.add(user)


class StaffApprovalForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['state', 'local_government']


class EditStaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['profile_picture','state', 'local_government', 'desired_chairman' ]
        
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'local_government': forms.Select(attrs={'class': 'form-control'}),
            'desired_chairman': forms.Select(attrs={'class': 'form-control'}),
        }


class StaffPostForm(forms.ModelForm):
    class Meta:
        model = StaffPost
        fields = [
            'title', 'description', 'image', 'video', 
            'state', 'local_government', 
            'location', 'latitude', 'longitude'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'local_government': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class StaffPostEditForm(forms.ModelForm):
    class Meta:
        model = StaffPost
        fields = ['title', 'description', 'image', 'video', 'state', 'local_government', 'chairman', 'location', 'latitude', 'longitude', 'status', 'feedback']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'cols': 40}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'video': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'local_government': forms.TextInput(attrs={'class': 'form-control'}),
            'chairman': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.HiddenInput(attrs={'class': 'form-control'}),
            'longitude': forms.HiddenInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control'}),
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
        model = Reply
        fields = ['text']

class StaffPostCommentForm(forms.ModelForm):
    class Meta:
        model = StaffPostComment
        fields = ['text']
        

class StaffPostReplyForm(forms.ModelForm):
    class Meta:
        model = StaffPostReply
        fields = ['text']
        