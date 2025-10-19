from django import forms
from django.contrib.auth import get_user_model
from django.core import validators as dj_validators

from main import models


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            "email",
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
    turnstile_response = forms.CharField(required=False)


class MemoryForm(forms.ModelForm):
    terms_of_service = forms.BooleanField()
    privacy_policy = forms.BooleanField()
    age_confirmation = forms.BooleanField()
    turnstile_response = forms.CharField(required=False)

    MEMORY_THEMES_CHOICES = [
        ("teacher-student relationships", "Teacher-student relationships"),
        ("school canteen", "School canteen"),
        ("break", "Break"),
        ("school yard", "School yard"),
        ("desk", "Desk"),
        ("classroom", "Classroom"),
        ("celebrations", "Celebrations"),
        ("excursions", "Excursions"),
        ("friendships", "Friendships"),
        ("school uniform", "School uniform"),
        ("school norms", "School norms"),
        ("school expulsion", "School expulsion"),
        ("mental health", "Mental health"),
        ("food", "Food"),
        ("learning styles", "Learning styles"),
        ("gendered toilets", "Gendered toilets"),
        ("nature", "Nature"),
        ("exams", "Exams"),
        ("hairstyles", "Hairstyles"),
    ]
    memory_themes = forms.MultipleChoiceField(
        choices=MEMORY_THEMES_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
    )
    memory_themes_additional = forms.CharField(
        required=False,
        max_length=500,
    )

    class Meta:
        model = models.Memory
        fields = [
            "age",
            "gender",
            "gender_other",
            "heritage",
            "country",
            "school_grade",
            "school_type",
            "school_type_other",
            "memory_themes",
            "memory_themes_additional",
            "title",
            "body",
        ]

    def clean(self):
        cleaned_data = super().clean()

        # handle gender
        gender = cleaned_data.get("gender")
        gender_other = cleaned_data.get("gender_other")
        if gender == "OTHER" and not gender_other:
            self.add_error(
                "gender_other",
                'Please specify how you self-identify when selecting "Other".',
            )
        if gender != "OTHER":
            cleaned_data["gender_other"] = None

        # handle school type
        school_type = cleaned_data.get("school_type")
        school_type_other = cleaned_data.get("school_type_other")
        if school_type == "OTHER" and not school_type_other:
            self.add_error(
                "school_type_other",
                'Please specify the school type when selecting "Other".',
            )
        if school_type != "OTHER":
            cleaned_data["school_type_other"] = None

        # handle memory themes
        memory_themes = cleaned_data.get("memory_themes")
        if memory_themes:
            cleaned_data["memory_themes"] = ",".join(memory_themes)

        # handle additional memory themes
        memory_themes_additional = cleaned_data.get("memory_themes_additional", "")
        if memory_themes_additional:
            additional_themes_list = [
                theme.strip()
                for theme in memory_themes_additional.split(";")
                if theme.strip()
            ]
            if len(additional_themes_list) > 5:
                self.add_error(
                    "memory_themes_additional",
                    "You can add a maximum of 5 custom themes.",
                )
            for theme in additional_themes_list:
                if len(theme) > 50:
                    self.add_error(
                        "memory_themes_additional",
                        f"Each theme must be 50 characters or less. Custom theme '{theme}' is too long.",
                    )
            cleaned_data["memory_themes_additional"] = ",".join(additional_themes_list)

        return cleaned_data


class IntroductionForm(forms.ModelForm):
    class Meta:
        model = models.SiteSettings
        fields = ["introduction"]


class PrivacyPolicyForm(forms.ModelForm):
    class Meta:
        model = models.SiteSettings
        fields = ["privacy_policy"]


class TermsOfServiceForm(forms.ModelForm):
    class Meta:
        model = models.SiteSettings
        fields = ["terms_of_service"]
