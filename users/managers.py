from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Создаёт пользователей и суперпользователей по email."""

    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            surname=surname,
            **extra_fields,
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
        self, email, name, surname, password=None, **extra_fields
    ):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        return self.create_user(email, name, surname, password, **extra_fields)
