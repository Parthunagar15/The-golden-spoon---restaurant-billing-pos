from django import forms
from .models import * 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')