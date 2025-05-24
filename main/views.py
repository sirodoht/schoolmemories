import uuid

import httpx
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjLogoutView
from django.core.mail import send_mail
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


def index(request):
    # filters
    country_filter = request.GET.get("country", "")
    gender_filter = request.GET.get("gender", "")
    ethnicity_filter = request.GET.get("ethnicity", "")
    school_grade_filter = request.GET.get("school_grade", "")
    school_type_filter = request.GET.get("school_type", "")
    memory_theme_filter = request.GET.get("memory_theme", "")
    memories = models.Memory.objects.all()
    if country_filter:
        memories = memories.filter(country=country_filter)
    if gender_filter:
        memories = memories.filter(gender=gender_filter)
    if ethnicity_filter:
        memories = memories.filter(ethnicity=ethnicity_filter)
    if school_grade_filter:
        memories = memories.filter(school_grade=school_grade_filter)
    if school_type_filter:
        # Handle both predefined choices and custom "other" entries
        if school_type_filter == "OTHER":
            memories = memories.filter(school_type="OTHER")
        else:
            # Check if it's a custom school type (from school_type_other field)
            custom_school_types = models.Memory.objects.filter(
                school_type="OTHER", school_type_other=school_type_filter
            ).values_list("id", flat=True)
            if custom_school_types.exists():
                memories = memories.filter(
                    school_type="OTHER", school_type_other=school_type_filter
                )
            else:
                memories = memories.filter(school_type=school_type_filter)
    if memory_theme_filter:
        # Search in both memory_themes and memory_themes_additional fields
        from django.db.models import Q

        memories = memories.filter(
            Q(memory_themes__icontains=memory_theme_filter)
            | Q(memory_themes_additional__icontains=memory_theme_filter)
        )
    filters_active = bool(
        country_filter
        or gender_filter
        or ethnicity_filter
        or school_grade_filter
        or school_type_filter
        or memory_theme_filter
    )

    # exclude countries of which there are no memories
    used_countries = models.Memory.objects.values_list("country", flat=True).distinct()
    countries = [
        (code, name)
        for code, name in models.Memory.COUNTRY_CHOICES
        if code in used_countries
    ]

    # show all gender options (not just those with memories)
    genders = models.Memory.GENDER_CHOICES

    # get unique ethnicity values (excluding empty/whitespace-only values)
    used_ethnicities = (
        models.Memory.objects.exclude(ethnicity__isnull=True)
        .exclude(ethnicity__exact="")
        .exclude(ethnicity__regex=r"^\s*$")
        .values_list("ethnicity", flat=True)
        .distinct()
        .order_by("ethnicity")
    )
    ethnicities = [(ethnicity, ethnicity) for ethnicity in used_ethnicities]

    # get unique school grade values (excluding empty/whitespace-only values)
    used_school_grades = (
        models.Memory.objects.exclude(school_grade__isnull=True)
        .exclude(school_grade__exact="")
        .exclude(school_grade__regex=r"^\s*$")
        .values_list("school_grade", flat=True)
        .distinct()
        .order_by("school_grade")
    )
    school_grades = [(grade, grade) for grade in used_school_grades]

    # get school type options (predefined choices + custom ones)
    school_types = []
    # Add predefined choices that have memories
    used_predefined_types = (
        models.Memory.objects.exclude(school_type="OTHER")
        .values_list("school_type", flat=True)
        .distinct()
    )
    for code, name in models.Memory.SCHOOL_TYPE_CHOICES:
        if code in used_predefined_types:
            school_types.append((code, name))

    # Add custom school types from school_type_other field
    custom_school_types = (
        models.Memory.objects.filter(school_type="OTHER")
        .exclude(school_type_other__isnull=True)
        .exclude(school_type_other__exact="")
        .exclude(school_type_other__regex=r"^\s*$")
        .values_list("school_type_other", flat=True)
        .distinct()
        .order_by("school_type_other")
    )
    for custom_type in custom_school_types:
        school_types.append((custom_type, custom_type))

    # get all unique memory themes (from both fields)
    all_themes = set()

    # Get themes from memory_themes field
    memory_themes_data = (
        models.Memory.objects.exclude(memory_themes__isnull=True)
        .exclude(memory_themes__exact="")
        .values_list("memory_themes", flat=True)
    )
    for themes_string in memory_themes_data:
        if themes_string:
            themes_list = [
                theme.strip() for theme in themes_string.split(",") if theme.strip()
            ]
            all_themes.update(themes_list)

    # Get themes from memory_themes_additional field
    additional_themes_data = (
        models.Memory.objects.exclude(memory_themes_additional__isnull=True)
        .exclude(memory_themes_additional__exact="")
        .values_list("memory_themes_additional", flat=True)
    )
    for themes_string in additional_themes_data:
        if themes_string:
            themes_list = [
                theme.strip() for theme in themes_string.split(",") if theme.strip()
            ]
            all_themes.update(themes_list)

    # Convert to sorted list of tuples
    memory_themes = [(theme, theme) for theme in sorted(all_themes)]

    return render(
        request,
        "main/memory_list.html",
        {
            "page_list": models.Page.objects.all().defer("body"),
            "memory_list": memories,
            "site_settings": models.SiteSettings.objects.first(),
            "countries": countries,
            "selected_country": country_filter,
            "genders": genders,
            "selected_gender": gender_filter,
            "ethnicities": ethnicities,
            "selected_ethnicity": ethnicity_filter,
            "school_grades": school_grades,
            "selected_school_grade": school_grade_filter,
            "school_types": school_types,
            "selected_school_type": school_type_filter,
            "memory_themes": memory_themes,
            "selected_memory_theme": memory_theme_filter,
            "filters_active": filters_active,
        },
    )


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
        if form.is_valid():
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
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        return context


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
        if word_count > 300:
            form.add_error(
                "body",
                f"Your memory text is {word_count} words but has to be less than 300",
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
            "Thank you for your submission. Here’s your memory ID number "
            f"#{obj.id}. Please, save this number in case you wish to reach out about "
            "something concerning your memory in the future"
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
            subject = f"[schoolmemories] New Memory Submission #{memory.id}"
            message = "A new memory has been submitted:\n\n"
            message += f"ID: {memory.id}\n"
            message += f"Title: {memory.title}\n"
            message += f"Location: {memory.get_country_display()}\n"
            message += f"Gender: {memory.get_gender_display()}\n"
            message += f"Ethnicity: {memory.ethnicity}\n"
            message += f"School Grade: {memory.school_grade}\n"
            message += f"School Type: {memory.get_school_type_display()}\n"
            message += f"Memory Themes: {memory.memory_themes}\n"
            if memory.memory_themes_additional:
                message += (
                    f"Additional Memory Themes: {memory.memory_themes_additional}\n"
                )
            message += f"Body:\n{memory.body}"
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
