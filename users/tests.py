import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project
from users.models import User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserModelTest(TestCase):
    """Модель пользователя и генерация аватарки."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="anna@example.com",
            name="Анна",
            surname="Иванова",
            password="pass12345",
        )

    def test_avatar_is_generated(self):
        """При создании пользователя аватарка заполняется сама."""
        self.assertTrue(self.user.avatar)

    def test_str(self):
        """В строковом виде пользователь — это имя и фамилия."""
        self.assertEqual(str(self.user), "Анна Иванова")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AuthTest(TestCase):
    """Регистрация и вход."""

    def test_registration_creates_user(self):
        """Валидная форма регистрации создаёт пользователя."""
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Иван",
                "surname": "Петров",
                "email": "ivan@example.com",
                "password": "pass12345",
            },
        )
        self.assertRedirects(response, reverse("projects:list"))
        self.assertTrue(User.objects.filter(email="ivan@example.com").exists())

    def test_login_with_wrong_password(self):
        """При неверном пароле вход не выполняется."""
        User.objects.create_user(
            email="maria@example.com",
            name="Мария",
            surname="Сидорова",
            password="pass12345",
        )
        response = self.client.post(
            reverse("users:login"),
            {"email": "maria@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProfileFormTest(TestCase):
    """Валидация телефона и ссылки на GitHub."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="anna@example.com",
            name="Анна",
            surname="Иванова",
            password="pass12345",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_phone_is_normalized(self):
        """Номер 8XXXXXXXXXX сохраняется как +7XXXXXXXXXX."""
        self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Анна",
                "surname": "Иванова",
                "about": "",
                "phone": "89991234567",
                "github_url": "",
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79991234567")

    def test_invalid_github_url(self):
        """Ссылка не на GitHub не сохраняется."""
        self.client.post(
            reverse("users:edit_profile"),
            {
                "name": "Анна",
                "surname": "Иванова",
                "about": "",
                "phone": "",
                "github_url": "https://example.com/anna",
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
            email="anna@example.com",
            name="Анна",
            surname="Иванова",
            password="pass12345",
        )
        cls.ivan = User.objects.create_user(
            email="ivan@example.com",
            name="Иван",
            surname="Петров",
            password="pass12345",
        )
        cls.project = Project.objects.create(name="Трекер", owner=cls.ivan)
        cls.anna.favorites.add(cls.project)

    def test_owners_of_favorite_projects(self):
        """Фильтр показывает авторов избранных проектов."""
        self.client.force_login(self.anna)
        response = self.client.get(
            reverse("users:list"),
            {"filter": "owners-of-favorite-projects"},
        )
        self.assertEqual(list(response.context["page_obj"]), [self.ivan])

    def test_interested_in_my_projects(self):
        """Фильтр показывает тех, кому нравятся мои проекты."""
        self.client.force_login(self.ivan)
        response = self.client.get(
            reverse("users:list"),
            {"filter": "interested-in-my-projects"},
        )
        self.assertEqual(list(response.context["page_obj"]), [self.anna])

    def test_filter_is_ignored_for_guest(self):
        """Гостю фильтр не применяется, виден весь список."""
        response = self.client.get(
            reverse("users:list"),
            {"filter": "owners-of-favorite-projects"},
        )
        self.assertEqual(len(response.context["page_obj"]), 2)


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
