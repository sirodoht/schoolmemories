from django.urls import include, path

from main import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
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
    path("accounts/edit/", views.UserUpdate.as_view(), name="user_update"),
]
