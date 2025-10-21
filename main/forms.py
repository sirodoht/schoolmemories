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

    educational_philosophy = forms.MultipleChoiceField(
        choices=models.Memory.EDUCATIONAL_PHILOSOPHY_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    class Meta:
        model = models.Memory
        fields = [
            "age",
            "gender",
            "gender_other",
            "heritage",
            "location",
            "country",
            "school_grade",
            "school_funding",
            "school_funding_other",
            "educational_philosophy",
            "educational_philosophy_other",
            "religious_tradition",
            "religious_tradition_other",
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

        # handle school funding
        school_funding = cleaned_data.get("school_funding")
        school_funding_other = cleaned_data.get("school_funding_other")
        if school_funding == "OTHER" and not school_funding_other:
            self.add_error(
                "school_funding_other",
                'Please specify the funding type when selecting "Other".',
            )
        if school_funding != "OTHER":
            cleaned_data["school_funding_other"] = None

        # handle educational philosophy
        educational_philosophy = cleaned_data.get("educational_philosophy")
        educational_philosophy_other = cleaned_data.get("educational_philosophy_other")
        if educational_philosophy:
            cleaned_data["educational_philosophy"] = ",".join(educational_philosophy)
            if "OTHER" in educational_philosophy and not educational_philosophy_other:
                self.add_error(
                    "educational_philosophy_other",
                    'Please specify the educational philosophy when selecting "Other".',
                )
        else:
            # Explicitly set to None when empty to avoid saving "[]"
            cleaned_data["educational_philosophy"] = None

        # handle religious tradition
        religious_tradition = cleaned_data.get("religious_tradition")
        religious_tradition_other = cleaned_data.get("religious_tradition_other")
        if religious_tradition == "OTHER" and not religious_tradition_other:
            self.add_error(
                "religious_tradition_other",
                'Please specify the religious tradition when selecting "Other".',
            )
        if religious_tradition != "OTHER":
            cleaned_data["religious_tradition_other"] = None

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
