from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("change-password/", views.change_password, name="change_password"),
    path("list/", views.participants, name="list"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("<int:user_id>/", views.user_detail, name="detail"),
]
