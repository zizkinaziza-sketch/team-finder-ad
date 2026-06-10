from django import forms

from team_finder.utils import validate_github_url

from .models import Project


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

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        validate_github_url(url)
        return url
