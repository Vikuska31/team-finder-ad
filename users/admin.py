from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка пользователя: ТЗ требует смену пароля и блокировку."""

    ordering = ("id",)
    list_display = ("email", "name", "surname", "is_active", "is_staff")
    search_fields = ("email", "name", "surname")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Профиль",
            {
                "fields": (
                    "name",
                    "surname",
                    "avatar",
                    "about",
                    "phone",
                    "github_url",
                )
            },
        ),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Избранное", {"fields": ("favorites",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "password1",
                    "password2",
                )
            },
        ),
    )
