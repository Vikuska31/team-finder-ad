from django.urls import path

from projects import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list, name="list"),
    path("create-project/", views.project_form, name="create"),
    path("<int:project_id>/", views.project_detail, name="detail"),
    path("<int:project_id>/edit/", views.project_form, name="edit"),
    path("<int:project_id>/complete/", views.complete, name="complete"),
    path(
        "<int:project_id>/toggle-participate/",
        views.toggle_participate,
        name="toggle_participate",
    ),
    path("favorites/", views.favorites, name="favorites"),
    path(
        "<int:project_id>/toggle-favorite/",
        views.toggle_favorite,
        name="toggle_favorite",
    ),
]
