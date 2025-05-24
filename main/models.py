import base64

import mistune
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse

from main import country, validators


class SiteSettings(models.Model):
    introduction = models.TextField(blank=True, null=True)
    terms_of_service = models.TextField(blank=True, null=True)
    privacy_policy = models.TextField(blank=True, null=True)

    @property
    def introduction_as_html(self):
        markdown = mistune.create_markdown(plugins=["task_lists", "footnotes"])
        return markdown(self.introduction)

    @property
    def terms_of_service_as_html(self):
        markdown = mistune.create_markdown(plugins=["task_lists", "footnotes"])
        return markdown(self.terms_of_service)

    @property
    def privacy_policy_as_html(self):
        markdown = mistune.create_markdown(plugins=["task_lists", "footnotes"])
        return markdown(self.privacy_policy)

    class Meta:
        verbose_name_plural = "Site Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Lowercase alphanumeric.",
        validators=[
            validators.AlphanumericHyphenValidator(),
            validators.HyphenOnlyValidator(),
        ],
        error_messages={"unique": "A user with that username already exists."},
    )
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class Page(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.CharField(
        max_length=300,
        validators=[validators.AlphanumericHyphenValidator()],
        help_text="Lowercase letters, numbers, and - (hyphen) allowed.",
    )
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True, null=True)

    @property
    def body_as_html(self):
        markdown = mistune.create_markdown(plugins=["task_lists", "footnotes"])
        return markdown(self.body)

    def __str__(self):
        return self.title


class Image(models.Model):
    name = models.CharField(max_length=300)  # original filename
    slug = models.CharField(max_length=300, unique=True)
    data = models.BinaryField()
    extension = models.CharField(max_length=10)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        return self.slug + "." + self.extension

    @property
    def data_as_base64(self):
        return base64.b64encode(self.data).decode("utf-8")

    @property
    def data_size(self):
        """Get image size in MB."""
        return round(len(self.data) / (1024 * 1024), 2)

    def get_raw_absolute_url(self):
        path = reverse(
            "image_raw", kwargs={"slug": self.slug, "extension": self.extension}
        )
        return f"{settings.PROTOCOL}//{settings.CANONICAL_HOST}{path}"

    def get_absolute_url(self):
        path = reverse("image_detail", kwargs={"slug": self.slug})
        return f"{settings.PROTOCOL}//{settings.CANONICAL_HOST}{path}"

    def __str__(self):
        return self.name


class Memory(models.Model):
    COUNTRY_CHOICES = [(code, name) for code, name in country.COUNTRIES.items()]
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    GENDER_CHOICES = [
        ("F", "Female"),
        ("M", "Male"),
        ("N", "Nonbinary"),
        ("O", "Other"),
        ("P", "Prefer not to say"),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    ethnicity = models.CharField(max_length=100)
    school_grade = models.CharField(max_length=16)
    SCHOOL_TYPE_CHOICES = [
        ("STATE", "State School"),
        ("PRIVATE", "Private School"),
        ("HOME", "Homeschooling"),
        ("COLLEGE", "College"),
        ("MONTESSORI", "Montessori School"),
        ("BOARDING", "Boarding School"),
        ("RELIGIOUS", "Religious School"),
        ("VOCATIONAL", "Vocational Education"),
        ("OTHER", "Other"),
    ]
    school_type = models.CharField(max_length=100, choices=SCHOOL_TYPE_CHOICES)
    school_type_other = models.CharField(max_length=100, blank=True, null=True)
    memory_themes = models.CharField(max_length=500)
    memory_themes_additional = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=100)
    body = models.TextField("Memory content")

    def get_school_type_display(self):
        if self.school_type == "OTHER" and self.school_type_other:
            return self.school_type_other
        choices = dict(self.SCHOOL_TYPE_CHOICES)
        return choices.get(self.school_type, self.school_type)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Memories"
