from django.urls import include, path

from main import views

urlpatterns = [
    path("", views.index, name="index"),
]


# user system
urlpatterns += [
    path("accounts/logout/", views.Logout.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "accounts/create/",
        views.UserCreate.as_view(),
        name="user_create",
    ),
]
