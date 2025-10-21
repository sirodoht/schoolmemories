import base64
import random

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

    def get_absolute_url(self):
        path = reverse("page_detail", kwargs={"slug": self.slug})
        return f"{settings.PROTOCOL}//{settings.CANONICAL_HOST}{path}"

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
    location = models.CharField(max_length=200, help_text="City/town/village")
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    age = models.IntegerField(choices=[(i, str(i)) for i in range(1, 19)], default=10)
    GENDER_CHOICES = [
        ("BOY", "Boy"),
        ("GIRL", "Girl"),
        ("OTHER", "Other"),
        ("PREFER_NOT_TO_SAY", "Prefer not to say"),
    ]
    gender = models.CharField(
        max_length=20, choices=GENDER_CHOICES, default="PREFER_NOT_TO_SAY"
    )
    gender_other = models.CharField(max_length=100, blank=True, null=True)
    heritage = models.CharField(max_length=100)
    school_grade = models.CharField(max_length=16)
    SCHOOL_FUNDING_CHOICES = [
        ("GOVERNMENT_STATE", "Government/State"),
        ("FAMILY", "Family"),
        ("SCHOLARSHIP_DONATIONS", "Scholarship/Donations"),
        ("OTHER", "Other"),
    ]
    school_funding = models.CharField(
        max_length=100, choices=SCHOOL_FUNDING_CHOICES, default="GOVERNMENT_STATE"
    )
    school_funding_other = models.CharField(max_length=200, blank=True, null=True)
    EDUCATIONAL_PHILOSOPHY_CHOICES = [
        ("MONTESSORI", "Montessori"),
        ("WALDORF", "Waldorf"),
        ("REGGIO_EMILIA", "Reggio Emilia"),
        ("PROGRESSIVE", "Progressive"),
        ("INTERNATIONAL_BACCALAUREATE", "International Baccalaureate"),
        ("FOREST_SCHOOL", "Forest School"),
        ("HOMESCHOOLING", "Homeschooling"),
        ("DOES_NOT_APPLY", "Does not apply"),
        ("OTHER", "Other"),
    ]
    educational_philosophy = models.CharField(max_length=500, blank=True, null=True)
    educational_philosophy_other = models.CharField(
        max_length=200, blank=True, null=True
    )
    RELIGIOUS_TRADITION_CHOICES = [
        ("QUAKER", "Quaker"),
        ("CATHOLIC", "Catholic"),
        ("PROTESTANT_CHRISTIAN", "Protestant/Christian"),
        ("JEWISH", "Jewish"),
        ("MUSLIM", "Muslim"),
        ("HINDU", "Hindu"),
        ("BUDDHIST", "Buddhist"),
        ("GREEK_ORTHODOX", "Greek Orthodox"),
        ("DOES_NOT_APPLY", "Does not apply"),
        ("OTHER", "Other"),
    ]
    religious_tradition = models.CharField(
        max_length=100, choices=RELIGIOUS_TRADITION_CHOICES, blank=True, null=True
    )
    religious_tradition_other = models.CharField(max_length=200, blank=True, null=True)
    memory_themes = models.CharField(max_length=500)
    memory_themes_additional = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=100)
    body = models.TextField("Memory content")
    code = models.CharField(max_length=20, blank=True, null=True)

    def get_school_funding_display(self):
        if self.school_funding == "OTHER" and self.school_funding_other:
            return self.school_funding_other
        choices = dict(self.SCHOOL_FUNDING_CHOICES)
        return choices.get(self.school_funding, self.school_funding)

    def get_educational_philosophy_display(self):
        if not self.educational_philosophy:
            return "Not specified"
        philosophies = self.educational_philosophy.split(",")
        display_names = []
        for phil in philosophies:
            phil = phil.strip()
            if phil == "OTHER" and self.educational_philosophy_other:
                display_names.append(self.educational_philosophy_other)
            else:
                choices = dict(self.EDUCATIONAL_PHILOSOPHY_CHOICES)
                display_names.append(choices.get(phil, phil))
        return ", ".join(display_names)

    def get_religious_tradition_display(self):
        if not self.religious_tradition:
            return "Not specified"
        if self.religious_tradition == "OTHER" and self.religious_tradition_other:
            return self.religious_tradition_other
        choices = dict(self.RELIGIOUS_TRADITION_CHOICES)
        return choices.get(self.religious_tradition, self.religious_tradition)

    def get_absolute_url(self):
        path = reverse("memory_detail", kwargs={"pk": self.pk})
        return f"{settings.PROTOCOL}//{settings.CANONICAL_HOST}{path}"

    def save(self, *args, **kwargs):
        # Save first to get the ID
        super().save(*args, **kwargs)
        # Generate code if it doesn't exist
        if not self.code:
            random_num = random.randint(100, 999)
            self.code = f"{self.id}-{random_num}"
            super().save(update_fields=["code"])

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Memories"
