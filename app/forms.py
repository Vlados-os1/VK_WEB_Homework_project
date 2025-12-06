from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, Question, Answer, Tag
from django.core.exceptions import ValidationError


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your login here'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Enter your password'})
    )



import logging
logger = logging.getLogger(__name__)


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email'
        })
    )
    nickname = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your nickname'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your login'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your email'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Login'
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Repeat password'

        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].widget.attrs.update({'class': 'form-input'})

        self.fields['username'].error_messages = {
            'required': 'Please enter a username.',
            'max_length': 'Username is too long (max 30 characters).',
            'unique': 'This username is already taken.',
        }
        self.fields['email'].error_messages = {
            'required': 'Please enter your email.',
            'invalid': 'Please enter a valid email address.',
            'unique': 'This email is already registered.',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if not username.isalnum():
            raise ValidationError("Username can only contain letters and numbers.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please use a different email or login.")
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not nickname:
            raise ValidationError("Please enter a nickname.")
        if len(nickname) < 2:
            raise ValidationError("Nickname must be at least 2 characters long.")
        return nickname

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Создаем профиль
            UserProfile.objects.create(
                user=user,
                nickname=self.cleaned_data['nickname']
            )

        return user


class SettingsForm(forms.ModelForm):
    login = forms.CharField(max_length=30, label="Login")
    email = forms.EmailField(max_length=50, label="Email")
    nickname = forms.CharField(max_length=30, label="NickName")
    avatar = forms.ImageField(required=False, label="Upload avatar")

    class Meta:
        model = UserProfile
        fields = ['nickname', 'avatar']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['login'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_login(self):
        login = self.cleaned_data.get('login')

        if not login:
            raise ValidationError("Username is required.")

        if len(login) < 3:
            raise ValidationError("Username must be at least 3 characters long.")

        if User.objects.filter(username=login).exclude(id=self.user.id).exists():
            raise ValidationError("Sorry, this username is already taken!")

        return login

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.user.id).exists():
            raise ValidationError("Sorry, this email address already registered!")
        return email


class AskForm(forms.ModelForm):
    tags = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'moon, park, puzzle'
        })
    )

    class Meta:
        model = Question
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'How to build a moon park ?',
                'maxlength': '100'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Really, how ?\nHave no idea about it',
                'maxlength': '1000',
                'rows': 10
            }),
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'answer-textarea',
                'placeholder': 'Your answer...',
                'rows': 4
            }),
        }