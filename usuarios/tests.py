from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Usuario


class UsuarioTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword123"
        )
        self.usuario_profile = self.user.usuario
        self.usuario_profile.telefono = "1234567890"
        self.usuario_profile.save()

    def test_usuario_str(self):
        self.assertEqual(str(self.usuario_profile), "testuser")

    def test_login_view_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_view_post_valid(self):
        response = self.client.post(
            reverse("login"), {"login": "testuser", "password": "testpassword123"}
        )
        self.assertRedirects(response, reverse("index"))

    def test_login_view_post_valid_email(self):
        response = self.client.post(
            reverse("login"),
            {"login": "test@example.com", "password": "testpassword123"},
        )
        self.assertRedirects(response, reverse("index"))

    def test_login_view_post_invalid(self):
        response = self.client.post(
            reverse("login"), {"login": "testuser", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credenciales inválidas")

    def test_logout_view(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("index"))

    def test_registro_view_get(self):
        response = self.client.get(reverse("registro"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registro.html")

    def test_registro_view_post_valid(self):
        response = self.client.post(
            reverse("registro"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "SecurePassword123!",
                "password2": "SecurePassword123!",
            },
        )
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertTrue(Usuario.objects.filter(user__username="newuser").exists())

    def test_perfil_view_unauthenticated(self):
        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_perfil_view_authenticated(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "perfil.html")

    def test_perfil_view_post(self):
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.post(
            reverse("perfil"),
            {
                "telefono": "0987654321",
                "first_name": "Updated",
                "last_name": "Name",
                "colonia": "",
                "calle": "",
                "ciudad": "",
                "estado": "",
                "codigo_postal": "",
            },
        )
        self.assertRedirects(response, reverse("perfil"))
        self.usuario_profile.refresh_from_db()
        self.assertEqual(self.usuario_profile.telefono, "0987654321")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
