# Generated by Django 5.2 on 2025-04-14 16:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0020_alter_sitesettings_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="privacy_policy",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="terms_of_service",
            field=models.TextField(blank=True, null=True),
        ),
    ]
