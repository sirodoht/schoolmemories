from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView as DjLogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from main import forms


def index(request):
    return render(request, "main/landing.html")


class UserCreate(CreateView):
    form_class = forms.UserCreationForm
    success_url = reverse_lazy("index")
    template_name = "main/user_create.html"
    success_message = "welcome :)"

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
