import mistune
from django.contrib.auth.models import AbstractUser
from django.db import models

from main import validators


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="This is your subdomain. Lowercase alphanumeric.",
        validators=[
            validators.AlphanumericHyphenValidator(),
            validators.HyphenOnlyValidator(),
        ],
        error_messages={"unique": "A user with that username already exists."},
    )
    email = models.EmailField(unique=True)
    website_title = models.CharField(max_length=500, blank=True, null=True)
    custom_domain = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        validators=[validators.validate_domain_name],
    )

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def body_as_html(self):
        markdown = mistune.create_markdown(plugins=["task_lists", "footnotes"])
        return markdown(self.body)

    def __str__(self):
        return self.title

    class Meta:
        unique_together = [["slug", "user"]]
