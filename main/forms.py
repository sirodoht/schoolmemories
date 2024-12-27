from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as DjUserCreationForm

from main import models


class UserCreationForm(DjUserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["username", "email", "website_title"]


class UserUpdateForm(forms.ModelForm):
    home = forms.ModelChoiceField(
        queryset=models.Page.objects.all(),
        required=False,
        empty_label="No home page",
    )

    class Meta:
        model = get_user_model()
        fields = ["username", "email", "website_title", "custom_domain", "home"]
