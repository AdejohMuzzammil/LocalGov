from django import forms
from .models import *
class ChairmanProfileForm(forms.ModelForm):
    class Meta:
        model = ChairmanProfile
        fields = ['profile_picture', 'bio', 'state', 'local_government', 'phone_number', 'email']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write something about yourself...'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
        }
