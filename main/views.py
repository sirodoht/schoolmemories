import uuid

import httpx
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjLogoutView
from django.core.mail import send_mail
from django.db.models import Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    TemplateView,
    UpdateView,
)

from main import forms, models


def extract_filters_from_request(request):
    """Extract all filter parameters from the request."""
    return {
        "country": request.GET.get("country", ""),
        "gender": request.GET.get("gender", ""),
        "heritage": request.GET.get("heritage", ""),
        "school_grade": request.GET.get("school_grade", ""),
        "school_funding": request.GET.get("school_funding", ""),
        "memory_theme": request.GET.get("memory_theme", ""),
    }


def get_non_empty_field_values(model_or_queryset, field_name):
    """Get unique non-empty values for a given field, excluding null, empty, and whitespace-only values."""
    # Handle both model classes and querysets
    if hasattr(model_or_queryset, "objects"):
        # It's a model class
        queryset = model_or_queryset.objects
    else:
        # It's already a queryset
        queryset = model_or_queryset

    return (
        queryset.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{f"{field_name}__exact": ""})
        .exclude(**{f"{field_name}__regex": r"^\s*$"})
        .values_list(field_name, flat=True)
        .distinct()
        .order_by(field_name)
    )


def apply_memory_filters(queryset, filters):
    """Apply all filters to the memory queryset."""
    if filters["country"]:
        queryset = queryset.filter(country=filters["country"])
    if filters["gender"]:
        queryset = queryset.filter(gender=filters["gender"])
    if filters["heritage"]:
        queryset = queryset.filter(heritage=filters["heritage"])
    if filters["school_grade"]:
        queryset = queryset.filter(school_grade=filters["school_grade"])
    if filters["school_funding"]:
        queryset = apply_school_funding_filter(queryset, filters["school_funding"])
    if filters["memory_theme"]:
        queryset = apply_memory_theme_filter(queryset, filters["memory_theme"])
    return queryset


def apply_school_funding_filter(queryset, school_funding_filter):
    """Apply school funding filter handling both predefined choices and custom 'other' entries."""
    if school_funding_filter == "OTHER":
        return queryset.filter(school_funding="OTHER")

    # Check if it's a custom school funding (from school_funding_other field)
    custom_school_fundings = models.Memory.objects.filter(
        school_funding="OTHER", school_funding_other=school_funding_filter
    ).values_list("id", flat=True)

    if custom_school_fundings.exists():
        return queryset.filter(
            school_funding="OTHER", school_funding_other=school_funding_filter
        )
    else:
        return queryset.filter(school_funding=school_funding_filter)


def apply_memory_theme_filter(queryset, memory_theme_filter):
    """Apply memory theme filter searching in both theme fields."""
    return queryset.filter(
        Q(memory_themes__icontains=memory_theme_filter)
        | Q(memory_themes_additional__icontains=memory_theme_filter)
    )


def build_filter_options():
    """Build all filter options for the template."""
    # Countries - exclude countries with no memories
    used_countries = models.Memory.objects.values_list("country", flat=True).distinct()
    countries = [
        (code, name)
        for code, name in models.Memory.COUNTRY_CHOICES
        if code in used_countries
    ]

    # School funding - predefined choices + custom ones
    school_fundings = []
    # Add predefined choices that have memories
    used_predefined_fundings = (
        models.Memory.objects.exclude(school_funding="OTHER")
        .values_list("school_funding", flat=True)
        .distinct()
    )
    for code, name in models.Memory.SCHOOL_FUNDING_CHOICES:
        if code in used_predefined_fundings:
            school_fundings.append((code, name))
    # Add custom school fundings from school_funding_other field
    custom_school_fundings = get_non_empty_field_values(
        models.Memory.objects.filter(school_funding="OTHER"), "school_funding_other"
    )
    for custom_funding in custom_school_fundings:
        school_fundings.append((custom_funding, custom_funding))

    # Memory themes - extract from both fields
    all_themes = set()
    # Get themes from memory_themes field
    memory_themes_data = get_non_empty_field_values(models.Memory, "memory_themes")
    for themes_string in memory_themes_data:
        if themes_string:
            themes_list = [
                theme.strip() for theme in themes_string.split(",") if theme.strip()
            ]
            all_themes.update(themes_list)
    # Get themes from memory_themes_additional field
    additional_themes_data = get_non_empty_field_values(
        models.Memory, "memory_themes_additional"
    )
    for themes_string in additional_themes_data:
        if themes_string:
            themes_list = [
                theme.strip() for theme in themes_string.split(",") if theme.strip()
            ]
            all_themes.update(themes_list)
    memory_themes = [(theme, theme) for theme in sorted(all_themes)]

    return {
        "countries": countries,
        "genders": models.Memory.GENDER_CHOICES,
        "heritages": [
            (heritage, heritage)
            for heritage in get_non_empty_field_values(models.Memory, "heritage")
        ],
        "school_grades": [
            (grade, grade)
            for grade in get_non_empty_field_values(models.Memory, "school_grade")
        ],
        "school_fundings": school_fundings,
        "memory_themes": memory_themes,
    }


def index(request):
    filters = extract_filters_from_request(request)
    memories = apply_memory_filters(models.Memory.objects.all(), filters)
    filter_options = build_filter_options()
    context = {
        "page_list": models.Page.objects.all().defer("body"),
        "memory_list": memories,
        "site_settings": models.SiteSettings.objects.first(),
        "countries": filter_options["countries"],
        "selected_country": filters["country"],
        "genders": filter_options["genders"],
        "selected_gender": filters["gender"],
        "heritages": filter_options["heritages"],
        "selected_heritage": filters["heritage"],
        "school_grades": filter_options["school_grades"],
        "selected_school_grade": filters["school_grade"],
        "school_fundings": filter_options["school_fundings"],
        "selected_school_funding": filters["school_funding"],
        "memory_themes": filter_options["memory_themes"],
        "selected_memory_theme": filters["memory_theme"],
        "filters_active": any(filters.values()),
    }
    return render(request, "main/memory_list.html", context)


class Logout(DjLogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "logged out")
        return super().dispatch(request, *args, **kwargs)


class UserUpdate(LoginRequiredMixin, UpdateView):
    form_class = forms.UserUpdateForm
    success_url = reverse_lazy("user_update")
    template_name = "main/user_update.html"

    def get_object(self):
        return self.request.user


@login_required
def dashboard(request):
    return render(
        request,
        "main/dashboard.html",
        {"page_list": models.Page.objects.all()},
    )


# Static Pages


class IntroductionUpdate(LoginRequiredMixin, UpdateView):
    model = models.SiteSettings
    form_class = forms.IntroductionForm
    template_name = "main/introduction_update.html"
    success_url = reverse_lazy("index")

    def get_object(self):
        return models.SiteSettings.load()


class PrivacyPolicyUpdate(LoginRequiredMixin, UpdateView):
    model = models.SiteSettings
    form_class = forms.PrivacyPolicyForm
    template_name = "main/privacy_policy_update.html"
    success_url = reverse_lazy("privacy_policy")

    def get_object(self):
        return models.SiteSettings.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        return context


class PrivacyPolicy(TemplateView):
    template_name = "main/privacy_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site_settings"] = models.SiteSettings.load()
        return context


class TermsOfServiceUpdate(LoginRequiredMixin, UpdateView):
    model = models.SiteSettings
    form_class = forms.TermsOfServiceForm
    template_name = "main/terms_of_service_update.html"
    success_url = reverse_lazy("terms_of_service")

    def get_object(self):
        return models.SiteSettings.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        return context


class TermsOfService(TemplateView):
    template_name = "main/terms_of_service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site_settings"] = models.SiteSettings.load()
        return context


# Pages


class PageCreate(LoginRequiredMixin, CreateView):
    model = models.Page
    fields = ["title", "slug", "body"]
    template_name = "main/page_create.html"

    def get_success_url(self):
        return reverse("page_detail", args=(self.object.slug,))


class PageDetail(DetailView):
    model = models.Page

    def get_success_url(self):
        return reverse("page_detail", args=(self.object.slug,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        return context


class PageUpdate(LoginRequiredMixin, UpdateView):
    model = models.Page
    fields = ["title", "slug", "body"]
    template_name = "main/page_update.html"

    def get_success_url(self):
        return reverse("page_detail", args=(self.object.slug,))

    def form_valid(self, form):
        if (
            models.Page.objects.filter(slug=form.cleaned_data.get("slug"))
            .exclude(id=self.object.id)
            .exists()
        ):
            form.add_error("slug", "This slug is already defined as one of your pages.")
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)


class PageDelete(LoginRequiredMixin, DeleteView):
    model = models.Page
    success_url = reverse_lazy("index")


# Images


class ImageList(LoginRequiredMixin, FormView):
    form_class = forms.UploadImagesForm
    template_name = "main/image_list.html"
    success_url = reverse_lazy("image_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["image_list"] = models.Image.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist("file")
        if form.is_valid():
            for f in files:
                name_ext_parts = f.name.rsplit(".", 1)
                name = name_ext_parts[0].replace(".", "-")
                self.extension = name_ext_parts[1].casefold()
                if self.extension == "jpg":
                    self.extension = "jpeg"
                data = f.read()

                # Image file limit 1.1MB = 1.1 * 1000^2
                if len(data) > 1.1 * 1000 * 1000:
                    form.add_error("file", "File too big. Limit is 1MB.")
                    return self.form_invalid(form)

                self.slug = str(uuid.uuid4())[:8]
                models.Image.objects.create(
                    name=name,
                    data=data,
                    extension=self.extension,
                    slug=self.slug,
                )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        # if ?raw=true in url, return to image_raw instead of image_list
        if (
            len(self.request.FILES.getlist("file")) == 1
            and self.request.GET.get("raw") == "true"
        ):
            return reverse("image_raw", args=(self.slug, self.extension))
        else:
            return str(self.success_url)  # success_url is lazy

    def form_invalid(self, form):
        # if ?raw=true in url, return form error as string
        if (
            len(self.request.FILES.getlist("file")) == 1
            and self.request.GET.get("raw") == "true"
        ):
            return HttpResponseBadRequest(" ".join(form.errors["file"]))
        else:
            return super().form_invalid(form)


class ImageDetail(LoginRequiredMixin, DetailView):
    model = models.Image


async def image_raw(request, slug, extension):
    image = await models.Image.objects.filter(slug=slug).afirst()
    if not image or extension != image.extension:
        raise Http404()
    return HttpResponse(image.data, content_type="image/" + image.extension)


class ImageUpdate(LoginRequiredMixin, UpdateView):
    model = models.Image
    fields = ["name"]
    template_name = "main/image_edit.html"


class ImageDelete(LoginRequiredMixin, DeleteView):
    model = models.Image
    success_url = reverse_lazy("image_list")


# Contact


class Contact(FormView):
    form_class = forms.ContactForm
    template_name = "main/contact.html"
    success_url = reverse_lazy("index")
    success_message = "message has been sent, thank you"

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if not form.is_valid():
            return self.form_invalid(form)

        # check if spam
        if settings.TURNSTILE_SECRET:
            turnstile_token = form.cleaned_data.get("turnstile_response")
            remote_ip = request.META.get("HTTP_X_FORWARDED_FOR")
            if not self.verify_turnstile(turnstile_token, remote_ip):
                form.add_error(None, "Captcha verification failed. Please try again.")
                return self.form_invalid(form)

        # process contact form
        superusers = models.User.objects.filter(is_superuser=True)
        superuser_emails = [user.email for user in superusers if user.email]
        if not superuser_emails:
            return self.form_valid(form)

        subject = f"[schoolmemories] Contact from {form.cleaned_data.get('name')}"
        message = f"Name: {form.cleaned_data.get('name')}\n"
        message += f"Email: {form.cleaned_data.get('email')}\n\n"
        message += f"Message:\n{form.cleaned_data.get('message')}"
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            superuser_emails,
        )

        messages.success(self.request, self.success_message)
        return self.form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        context["enable_turnstile"] = bool(settings.TURNSTILE_SECRET)
        return context

    def verify_turnstile(self, token, remote_ip):
        data = {
            "secret": settings.TURNSTILE_SECRET,
            "response": token,
            "remoteip": remote_ip,
        }
        response = httpx.post(url=settings.TURNSTILE_URL, data=data, timeout=5.0)
        return response.json().get("success", False)


# Memories


class MemoryCreate(FormView):
    form_class = forms.MemoryForm
    template_name = "main/memory_create.html"
    success_url = reverse_lazy("index")

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if not form.is_valid():
            return self.form_invalid(form)

        # check if spam
        if settings.TURNSTILE_SECRET:
            turnstile_token = form.cleaned_data.get("turnstile_response")
            remote_ip = request.META.get("HTTP_X_FORWARDED_FOR")
            if not self.verify_turnstile(turnstile_token, remote_ip):
                form.add_error(None, "Captcha verification failed. Please try again.")
                return self.form_invalid(form)

        # process memory form data
        body_text = form.cleaned_data.get("body")
        word_count = len(body_text.split())
        if word_count > 1000:
            form.add_error(
                "body",
                f"Your memory text is {word_count} words but has to be less than 1000",
            )
            return self.form_invalid(form)

        # check ToS and privacy policy
        if not form.cleaned_data.get("terms_of_service"):
            form.add_error(
                "terms_of_service",
                "You must accept the Terms of Service to continue.",
            )
            return self.form_invalid(form)
        if not form.cleaned_data.get("privacy_policy"):
            form.add_error(
                "privacy_policy", "You must accept the Privacy Policy to continue."
            )
            return self.form_invalid(form)
        if not form.cleaned_data.get("age_confirmation"):
            form.add_error(
                "age_confirmation", "You must be over 18 years old to continue."
            )
            return self.form_invalid(form)

        obj = form.save()
        message = (
            "Thank you for your submission. Here’s your memory code number "
            f"#{obj.code}. Please, save this number in case you wish to reach out about"
            " something concerning your memory in the future."
        )
        messages.success(self.request, message)
        if settings.LOCALDEV or (
            settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD
        ):
            self.send_notification_email(obj)
        return self.form_valid(form)

    def send_notification_email(self, memory):
        superusers = models.User.objects.filter(is_superuser=True)
        superuser_emails = [user.email for user in superusers if user.email]
        if superuser_emails:
            subject = f"[schoolmemories] New Memory Submission #{memory.code}"
            message = "A new memory has been submitted:\n\n"
            message += f"Code: {memory.code}\n"
            message += f"Link: {memory.get_absolute_url()}\n\n"
            message += f"Age: {memory.age} years old\n"
            message += f"Location: {memory.location}, {memory.get_country_display()}\n"
            message += f"Gender: {memory.get_gender_display()}"
            if memory.gender_other:
                message += f" ({memory.gender_other})"
            message += f"\nHeritage: {memory.heritage}\n\n"
            message += f"School Grade: {memory.school_grade}\n"
            message += f"School Funding: {memory.get_school_funding_display()}\n"
            if memory.educational_philosophy:
                message += f"Educational Philosophy: {memory.get_educational_philosophy_display()}\n"
            if memory.religious_tradition:
                message += f"Religious Tradition: {memory.get_religious_tradition_display()}\n"
            message += f"\nTitle: {memory.title}\n"
            message += f"Memory Themes: {memory.memory_themes}\n"
            if memory.memory_themes_additional:
                message += (
                    f"Additional Memory Themes: {memory.memory_themes_additional}\n"
                )
            message += f"Memory Text:\n{memory.body}"
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                superuser_emails,
            )

    def verify_turnstile(self, token, remote_ip):
        data = {
            "secret": settings.TURNSTILE_SECRET,
            "response": token,
            "remoteip": remote_ip,
        }
        response = httpx.post(url=settings.TURNSTILE_URL, data=data, timeout=5.0)
        return response.json().get("success", False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        context["enable_turnstile"] = bool(settings.TURNSTILE_SECRET)
        return context


class MemoryDetail(DetailView):
    model = models.Memory
    template_name = "main/memory_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        return context
