import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjLogoutView
from django.core.exceptions import PermissionDenied
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from main import forms, models

logger = logging.getLogger(__name__)


@login_required
def landing(request):
    """
    Landing view for the convenience of logged in users only.
    """
    return render(request, "main/landing.html")


def index(request):
    logger.debug("index begin")

    # Account site mode as reader/enduser
    if hasattr(request, "subdomain"):
        logger.debug("reader visit")
        logger.debug(f"{request.subdomain=}")
        if models.User.objects.filter(username=request.subdomain).exists():
            if request.account_user.home:
                return render(
                    request,
                    "main/page_detail.html",
                    {
                        "canonical_url": f"{settings.PROTOCOL}//{settings.CANONICAL_HOST}",
                        "page": request.account_user.home,
                        "subdomain": request.subdomain,
                        "account_user": request.account_user,
                        "page_list": models.Page.objects.filter(
                            user=request.account_user
                        ).defer("body"),
                    },
                )
            else:
                return render(
                    request,
                    "main/account_index.html",
                    {
                        "canonical_url": f"{settings.PROTOCOL}//{settings.CANONICAL_HOST}",
                        "subdomain": request.subdomain,
                        "account_user": request.account_user,
                        "page_list": models.Page.objects.filter(
                            user=request.account_user
                        ).defer("body"),
                    },
                )
        else:
            return redirect("//" + settings.CANONICAL_HOST + reverse("index"))
    else:
        logger.debug("not a reader visit")

    logger.debug(f"{request.user.is_authenticated=}")

    # Account site as owner:
    # Redirect to "account_index" so that the requests gets a subdomain
    if request.user.is_authenticated:
        logger.debug("owner visit")
        return redirect(
            f'//{request.user.username}.{settings.CANONICAL_HOST}{reverse("index")}'
        )
    else:
        logger.debug("not an owner visit")

    logger.debug("render landing")

    # Landing site as non-logged-in user
    return render(request, "main/landing.html")


def domain_check(request):
    """
    This view returns 200 if domain given exists as custom domain in any user account.
    """
    url = request.GET.get("domain")
    if not url:
        raise PermissionDenied()

    # Landing case
    if url == settings.CANONICAL_HOST:
        return HttpResponse()

    # Custom domain case, can by anything
    if models.User.objects.filter(custom_domain=url).exists():
        return HttpResponse()

    # Subdomain case, can only by <username>.dukkha.pub
    if len(url.split(".")) != 3:
        raise PermissionDenied()

    username = url.split(".")[0]
    if models.User.objects.filter(username=username).exists():
        return HttpResponse()

    raise PermissionDenied()


class UserCreate(CreateView):
    form_class = forms.UserCreationForm
    success_message = "welcome :)"
    success_url = reverse_lazy("index")
    template_name = "main/user_create.html"

    def form_valid(self, form):
        self.object = form.save()
        user = authenticate(
            username=form.cleaned_data.get("username"),
            password=form.cleaned_data.get("password1"),
        )
        login(self.request, user)
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())


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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["home"].queryset = models.Page.objects.filter(
            user=self.request.user
        )
        return form


@login_required
def dashboard(request):
    if hasattr(request, "subdomain"):
        return redirect("//" + settings.CANONICAL_HOST + reverse("dashboard"))

    return render(
        request,
        "main/dashboard.html",
        {
            "page_list": models.Page.objects.filter(user=request.user),
            "blog_url": request.user.blog_url,
        },
    )


class PageCreate(LoginRequiredMixin, CreateView):
    model = models.Page
    fields = ["title", "slug", "body"]
    template_name = "main/page_create.html"
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class PageDetail(DetailView):
    model = models.Page

    def get_success_url(self):
        return reverse("page_detail", args=(self.object.slug,))

    def get_queryset(self):
        return models.Page.objects.filter(user__username=self.request.subdomain)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["canonical_url"] = f"{settings.PROTOCOL}//{settings.CANONICAL_HOST}"
        if hasattr(self.request, "subdomain"):
            context["account_user"] = self.request.account_user
            context["page_list"] = models.Page.objects.filter(
                user__username=self.request.subdomain
            )

        return context


class PageUpdate(LoginRequiredMixin, UpdateView):
    model = models.Page
    fields = ["title", "slug", "body"]
    template_name = "main/page_update.html"

    def get_success_url(self):
        return reverse("page_detail", args=(self.object.slug,))

    def get_queryset(self):
        return models.Page.objects.filter(user__username=self.request.subdomain)

    def form_valid(self, form):
        if (
            models.Page.objects.filter(
                user=self.request.user, slug=form.cleaned_data.get("slug")
            )
            .exclude(id=self.object.id)
            .exists()
        ):
            form.add_error("slug", "This slug is already defined as one of your pages.")
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if request.user != page.user:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class PageDelete(LoginRequiredMixin, DeleteView):
    model = models.Page
    success_url = reverse_lazy("index")

    def get_queryset(self):
        return models.Page.objects.filter(user__username=self.request.subdomain)

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if request.user != page.user:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class CSSUpdate(LoginRequiredMixin, UpdateView):
    model = models.User
    fields = ["custom_css"]
    template_name = "main/custom_css.html"
    success_url = reverse_lazy("css_update")

    def get_object(self):
        return self.request.user
