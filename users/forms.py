import re

from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import User


def normalize_phone(phone):
    if phone.startswith("8"):
        return "+7" + phone[1:]
    return phone


def validate_phone_format(phone):
    pattern = re.compile(r"^(8\d{10}|\+7\d{10})$")
    if not pattern.match(phone):
        raise ValidationError(
            "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
        )


def validate_github_url(url):
    if url and "github.com" not in url:
        raise ValidationError("URL должен быть на github.com")


class RegisterForm(forms.Form):
    name = forms.CharField(label="Имя", max_length=124)
    surname = forms.CharField(label="Фамилия", max_length=124)
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже зарегистрирован")
        return email

    def save(self):
        data = self.cleaned_data
        return User.objects.create_user(
            email=data["email"],
            name=data["name"],
            surname=data["surname"],
            password=data["password"],
        )


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise ValidationError("Неверный имейл или пароль")
            cleaned_data["user"] = user
        return cleaned_data


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone:
            return None
        validate_phone_format(phone)
        normalized = normalize_phone(phone)
        qs = User.objects.filter(phone=normalized)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Этот номер телефона уже используется")
        return normalized

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        validate_github_url(url)
        return url


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="Текущий пароль", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput)
    new_password2 = forms.CharField(
        label="Подтвердите новый пароль", widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise ValidationError("Текущий пароль неверен")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Пароли не совпадают")
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save()
