import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjLogoutView
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
    UpdateView,
)

from main import forms, models


def index(request):
    return render(
        request,
        "main/memory_list.html",
        {
            "page_list": models.Page.objects.all().defer("body"),
            "memory_list": models.Memory.objects.all(),
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


class CSSUpdate(LoginRequiredMixin, UpdateView):
    model = models.User
    fields = ["custom_css"]
    template_name = "main/custom_css.html"
    success_url = reverse_lazy("css_update")

    def get_object(self):
        return self.request.user


@login_required
def dashboard(request):
    return render(
        request,
        "main/dashboard.html",
        {"page_list": models.Page.objects.all()},
    )


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
            # TODO: Email account user with message info
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
        if form.is_valid():
            obj = form.save()
            message = (
                f"Your Submission ID is #{obj.id}. Note it down for future reference."
            )
            messages.success(self.request, message)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_list"] = models.Page.objects.all()
        return context
