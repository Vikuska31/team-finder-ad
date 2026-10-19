import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project
from users.models import User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProjectListTest(TestCase):
    """Главная страница со списком проектов."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="anna@example.com",
            name="Анна",
            surname="Иванова",
            password="pass12345",
        )
        cls.old = Project.objects.create(name="Старый", owner=cls.user)
        cls.new = Project.objects.create(name="Новый", owner=cls.user)

    def test_root_redirects_to_list(self):
        """Корневой адрес ведёт на список проектов."""
        response = self.client.get("/")
        self.assertRedirects(response, reverse("projects:list"))

    def test_projects_sorted_from_new_to_old(self):
        """Проекты отсортированы от новых к старым."""
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(
            list(response.context["page_obj"]),
            [self.new, self.old],
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProjectCreateTest(TestCase):
    """Создание проекта."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="anna@example.com",
            name="Анна",
            surname="Иванова",
            password="pass12345",
        )

    def test_author_becomes_participant(self):
        """Автор нового проекта сразу становится участником."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("projects:create"),
            {
                "name": "Карта прогулок",
                "description": "Описание",
                "github_url": "",
                "status": Project.Status.OPEN,
            },
        )
        project = Project.objects.get(name="Карта прогулок")
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())

    def test_guest_cannot_create(self):
        """Гостя форма создания отправляет на страницу входа."""
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, 302)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProjectActionsTest(TestCase):
    """Завершение проекта, участие и избранное."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="anna@example.com",
            name="Анна",
            surname="Иванова",
            password="pass12345",
        )
        cls.guest = User.objects.create_user(
            email="ivan@example.com",
            name="Иван",
            surname="Петров",
            password="pass12345",
        )
        cls.project = Project.objects.create(name="Трекер", owner=cls.owner)

    def test_owner_completes_project(self):
        """Автор закрывает проект, статус меняется на closed."""
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("projects:complete", args=[self.project.id])
        )
        self.project.refresh_from_db()
        self.assertEqual(
            response.json(),
            {"status": "ok", "project_status": "closed"},
        )
        self.assertEqual(self.project.status, Project.Status.CLOSED)

    def test_stranger_cannot_complete_project(self):
        """Чужой пользователь закрыть проект не может."""
        self.client.force_login(self.guest)
        self.client.post(reverse("projects:complete", args=[self.project.id]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.OPEN)

    def test_toggle_participate(self):
        """Повторное нажатие добавляет и убирает участника."""
        self.client.force_login(self.guest)
        url = reverse("projects:toggle_participate", args=[self.project.id])
        self.client.post(url)
        self.assertIn(self.guest, self.project.participants.all())
        self.client.post(url)
        self.assertNotIn(self.guest, self.project.participants.all())

    def test_toggle_favorite(self):
        """Повторное нажатие добавляет и убирает избранное."""
        self.client.force_login(self.guest)
        url = reverse("projects:toggle_favorite", args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.json(), {"status": "ok", "favorited": True})
        self.assertIn(self.project, self.guest.favorites.all())
        response = self.client.post(url)
        self.assertEqual(response.json(), {"status": "ok", "favorited": False})
        self.assertNotIn(self.project, self.guest.favorites.all())

    def test_favorites_page_shows_only_own(self):
        """На странице избранного только проекты этого пользователя."""
        self.guest.favorites.add(self.project)
        self.client.force_login(self.guest)
        response = self.client.get(reverse("projects:favorites"))
        self.assertEqual(list(response.context["projects"]), [self.project])

    def test_guest_cannot_open_favorites(self):
        """Гостя страница избранного отправляет на вход."""
        response = self.client.get(reverse("projects:favorites"))
        self.assertEqual(response.status_code, 302)


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
