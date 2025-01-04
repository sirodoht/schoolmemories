from django.urls import include, path

from main import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("landing/", views.landing, name="landing"),
    path("css/update/", views.CSSUpdate.as_view(), name="css_update"),
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
    path("accounts/domain/", views.domain_check, name="domain_check"),
]

# pages - needs to be last due to <slug>
urlpatterns += [
    path("new/page/", views.PageCreate.as_view(), name="page_create"),
    path("<slug:slug>/", views.PageDetail.as_view(), name="page_detail"),
    path("<slug:slug>/edit/", views.PageUpdate.as_view(), name="page_update"),
    path("<slug:slug>/delete/", views.PageDelete.as_view(), name="page_delete"),
]
