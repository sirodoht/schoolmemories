from django import forms
from django.contrib.auth import get_user_model
from django.core import validators as dj_validators

from main import models


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            "email",
            "website_title",
        ]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, list | tuple):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class UploadImagesForm(forms.Form):
    file = MultipleFileField(
        validators=[
            dj_validators.FileExtensionValidator(["jpeg", "jpg", "png", "gif", "webp"])
        ],
    )


class ContactForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)


class MemoryForm(forms.ModelForm):
    terms_of_service = forms.BooleanField()
    privacy_policy = forms.BooleanField()

    class Meta:
        model = models.Memory
        fields = [
            "gender",
            "country",
            "category",
            "tags",
            "school_grade",
            "school_type",
            "title",
            "body",
        ]
