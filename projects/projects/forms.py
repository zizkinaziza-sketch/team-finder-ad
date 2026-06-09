from django import forms
from django.core.exceptions import ValidationError

from .models import Project


def validate_github_url(url):
    if url and "github.com" not in url:
        raise ValidationError("URL должен быть на github.com")


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название",
            "description": "Описание",
            "github_url": "GitHub",
            "status": "Статус",
        }
        widgets = {
            "status": forms.Select(
                choices=[("open", "Открыт"), ("closed", "Закрыт")]
            ),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        validate_github_url(url)
        return url
