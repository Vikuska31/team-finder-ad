from django.conf import settings
from django.db import models
from team_finder.validators import validate_github_url

from projects.constants import NAME_MAX_LENGTH


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField("Название", max_length=NAME_MAX_LENGTH)
    description = models.TextField("Описание проекта", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    github_url = models.URLField(
        "Ссылка на GitHub",
        blank=True,
        validators=[validate_github_url],
    )
    status = models.CharField(
        "Статус",
        max_length=max(len(value) for value, _ in Status.choices),
        choices=Status.choices,
        default=Status.OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="Участники",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    def __str__(self):
        return self.name
