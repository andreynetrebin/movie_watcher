from django import forms
from django.contrib.auth import get_user_model

from .models import Profile
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
            'max_length': 'Пароль должен содержать не более 150 символов.',
        },
        help_text='Пароль должен содержать не менее 8 символов и включать буквы и цифры.'  # Ваш текст
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
            'max_length': 'Пароль должен содержать не более 150 символов.',
        },
        help_text='Введите тот же пароль, что и выше, для подтверждения.'  # Ваш текст
    )
    username = forms.CharField(
        label='Имя пользователя',
        help_text='Имя пользователя должно содержать только буквы, цифры и символы @/./+/-/_.'  # Ваш текст
    )
    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'email']
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'email': 'Электронная почта',
        }
        error_messages = {
            'username': {
                'required': 'Это поле обязательно для заполнения.',
                'max_length': 'Имя пользователя должно содержать не более 150 символов.',
                'invalid': 'Используйте только буквы, цифры и символы @/./+/-/_',
            },
            'first_name': {
                'required': 'Это поле обязательно для заполнения.',
                'max_length': 'Имя должно содержать не более 150 символов.',
            },
            'email': {
                'required': 'Это поле обязательно для заполнения.',
                'invalid': 'Введите корректный адрес электронной почты.',
            },
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Пароли не совпадают.")
        return cd['password2']

    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Такой email уже используется')
        return data

class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
        }

    def clean_email(self):
        data = self.cleaned_data['email']
        qs = User.objects.exclude(
            id=self.instance.id
        ).filter(
            email=data
        )
        if qs.exists():
            raise forms.ValidationError('Такой email уже используется')
        return data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['date_of_birth', 'photo']
        labels = {
            'date_of_birth': 'День рождения',
            'photo': 'Аватар',
        }
