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
    category_filter = request.GET.get("category", "")
    memories = models.Memory.objects.all()
    if country_filter:
        memories = memories.filter(country=country_filter)
    if category_filter:
        memories = memories.filter(category=category_filter)
    filters_active = bool(country_filter or category_filter)

    categories = (
        models.Memory.objects.values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    # exclude countries of which there are no memories
    used_countries = models.Memory.objects.values_list("country", flat=True).distinct()
    countries = [
        (code, name)
        for code, name in models.Memory.COUNTRY_CHOICES
        if code in used_countries
    ]

    return render(
        request,
        "main/memory_list.html",
        {
            "page_list": models.Page.objects.all().defer("body"),
            "memory_list": memories,
            "site_settings": models.SiteSettings.objects.first(),
            "countries": countries,
            "selected_country": country_filter,
            "categories": categories,
            "selected_category": category_filter,
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
            form.add_error("body", "Your memory cannot exceed 300 words.")
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
            message += f"Category: {memory.category}\n"
            message += f"Tags: {memory.tags}\n\n"
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
