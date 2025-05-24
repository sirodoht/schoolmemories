from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from main import models

admin.site.site_header = "Admin Panel"


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "created_at", "updated_at")
    search_fields = ("title", "slug", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("created_at", "updated_at")


@admin.register(models.Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "extension", "data_size", "uploaded_at")
    search_fields = ("name", "slug")
    readonly_fields = ("uploaded_at", "data_size")
    list_filter = ("extension", "uploaded_at")


@admin.register(models.Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "code",
        "country",
        "gender",
        "school_grade",
        "school_type",
        "school_type_other",
    )
    search_fields = (
        "title",
        "body",
        "school_type",
        "school_type_other",
        "memory_themes",
        "memory_themes_additional",
    )
    list_filter = ("country", "gender", "school_type", "school_grade")
    readonly_fields = (
        "id",
        "code",
        "country",
        "gender",
        "ethnicity",
        "school_grade",
        "school_type",
        "school_type_other",
        "memory_themes",
        "memory_themes_additional",
        "title",
        "body",
    )
