import shutil
import tempfile
from http import HTTPStatus

from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project
from users.constants import (
    FILTER_FAVORITE_OWNERS,
    FILTER_INTERESTED_USERS,
)
from users.models import User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()

ANNA_EMAIL = "anna@example.com"
ANNA_NAME = "Анна"
ANNA_SURNAME = "Иванова"
IVAN_EMAIL = "ivan@example.com"
IVAN_NAME = "Иван"
IVAN_SURNAME = "Петров"
MARIA_EMAIL = "maria@example.com"
MARIA_NAME = "Мария"
MARIA_SURNAME = "Сидорова"
PASSWORD = "pass12345"
WRONG_PASSWORD = "wrong"
PROJECT_NAME = "Трекер"
RAW_PHONE = "89991234567"
NORMALIZED_PHONE = "+79991234567"
WRONG_GITHUB_URL = "https://example.com/anna"


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserModelTest(TestCase):
    """Модель пользователя и генерация аватарки."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email=ANNA_EMAIL,
            name=ANNA_NAME,
            surname=ANNA_SURNAME,
            password=PASSWORD,
        )

    def test_avatar_is_generated(self):
        """При создании пользователя аватарка заполняется сама."""
        self.assertTrue(self.user.avatar)

    def test_str(self):
        """В строковом виде пользователь — это имя и фамилия."""
        self.assertEqual(str(self.user), f"{ANNA_NAME} {ANNA_SURNAME}")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AuthTest(TestCase):
    """Регистрация и вход."""

    def test_registration_creates_user(self):
        """Валидная форма регистрации создаёт пользователя."""
        response = self.client.post(
            reverse("users:register"),
            {
                "name": IVAN_NAME,
                "surname": IVAN_SURNAME,
                "email": IVAN_EMAIL,
                "password": PASSWORD,
            },
        )
        self.assertRedirects(response, reverse("projects:list"))
        self.assertTrue(User.objects.filter(email=IVAN_EMAIL).exists())

    def test_login_with_wrong_password(self):
        """При неверном пароле вход не выполняется."""
        User.objects.create_user(
            email=MARIA_EMAIL,
            name=MARIA_NAME,
            surname=MARIA_SURNAME,
            password=PASSWORD,
        )
        response = self.client.post(
            reverse("users:login"),
            {"email": MARIA_EMAIL, "password": WRONG_PASSWORD},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(response.context["user"].is_authenticated)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProfileFormTest(TestCase):
    """Валидация телефона и ссылки на GitHub."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email=ANNA_EMAIL,
            name=ANNA_NAME,
            surname=ANNA_SURNAME,
            password=PASSWORD,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_phone_is_normalized(self):
        """Номер 8XXXXXXXXXX сохраняется как +7XXXXXXXXXX."""
        self.client.post(
            reverse("users:edit_profile"),
            {
                "name": ANNA_NAME,
                "surname": ANNA_SURNAME,
                "about": "",
                "phone": RAW_PHONE,
                "github_url": "",
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, NORMALIZED_PHONE)

    def test_invalid_github_url(self):
        """Ссылка не на GitHub не сохраняется."""
        self.client.post(
            reverse("users:edit_profile"),
            {
                "name": ANNA_NAME,
                "surname": ANNA_SURNAME,
                "about": "",
                "phone": "",
                "github_url": WRONG_GITHUB_URL,
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_url, "")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ParticipantsFilterTest(TestCase):
    """Фильтрация пользователей на странице участников."""

    @classmethod
    def setUpTestData(cls):
        cls.anna = User.objects.create_user(
            email=ANNA_EMAIL,
            name=ANNA_NAME,
            surname=ANNA_SURNAME,
            password=PASSWORD,
        )
        cls.ivan = User.objects.create_user(
            email=IVAN_EMAIL,
            name=IVAN_NAME,
            surname=IVAN_SURNAME,
            password=PASSWORD,
        )
        cls.project = Project.objects.create(name=PROJECT_NAME, owner=cls.ivan)
        cls.anna.favorites.add(cls.project)

    def test_owners_of_favorite_projects(self):
        """Фильтр показывает авторов избранных проектов."""
        self.client.force_login(self.anna)
        response = self.client.get(
            reverse("users:list"),
            {"filter": FILTER_FAVORITE_OWNERS},
        )
        self.assertEqual(list(response.context["page_obj"]), [self.ivan])

    def test_interested_in_my_projects(self):
        """Фильтр показывает тех, кому нравятся мои проекты."""
        self.client.force_login(self.ivan)
        response = self.client.get(
            reverse("users:list"),
            {"filter": FILTER_INTERESTED_USERS},
        )
        self.assertEqual(list(response.context["page_obj"]), [self.anna])

    def test_filter_is_ignored_for_guest(self):
        """Гостю фильтр не применяется, виден весь список."""
        response = self.client.get(
            reverse("users:list"),
            {"filter": FILTER_FAVORITE_OWNERS},
        )
        self.assertEqual(len(response.context["page_obj"]), 2)


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
