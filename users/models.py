import random
import uuid
from io import BytesIO

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont

from team_finder.validators import validate_github_url
from users.constants import (
    ABOUT_MAX_LENGTH,
    AVATAR_COLORS,
    AVATAR_FONT_SIZE,
    AVATAR_SIZE,
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    SURNAME_MAX_LENGTH,
)


class UserManager(BaseUserManager):
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


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        "Email",
        max_length=EMAIL_MAX_LENGTH,
        unique=True
    )
    name = models.CharField("Имя", max_length=NAME_MAX_LENGTH)
    surname = models.CharField("Фамилия", max_length=SURNAME_MAX_LENGTH)
    avatar = models.ImageField("Аватар", upload_to="avatars/")
    phone = models.CharField(
        "Телефон",
        max_length=PHONE_MAX_LENGTH,
        unique=True,
        null=True,
        blank=True,
    )
    github_url = models.URLField(
        "Ссылка на GitHub",
        blank=True,
        validators=[validate_github_url],
    )
    about = models.TextField("О себе", max_length=ABOUT_MAX_LENGTH, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Администратор", default=False)
    favorites = models.ManyToManyField(
        "projects.Project",
        related_name="interested_users",
        blank=True,
        verbose_name="Избранные проекты",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            image = Image.new(
                "RGB",
                (AVATAR_SIZE, AVATAR_SIZE),
                random.choice(AVATAR_COLORS),
            )
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default(size=AVATAR_FONT_SIZE)
            draw.text(
                (AVATAR_SIZE // 2, AVATAR_SIZE // 2),
                self.name[0].upper(),
                fill="white",
                font=font,
                anchor="mm",
            )
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            self.avatar.save(
                f"avatar_{uuid.uuid4()}.png",
                ContentFile(buffer.getvalue()),
                save=False,
            )
        super().save(*args, **kwargs)
