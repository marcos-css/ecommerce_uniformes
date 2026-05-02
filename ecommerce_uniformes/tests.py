from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import json
from .models import (
    Pedido,
    Producto,
    Categoria,
    Escuela,
    Color,
    Talla,
    ColorProducto,
    TallaVariante,
    Favoritos,
    DetallesPedido,
    HistorialStock,
)


class EcommerceModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.categoria = Categoria.objects.create(nombre="Uniformes")
        self.escuela = Escuela.objects.create(nombre="Escuela Secundaria")
        self.color = Color.objects.create(nombre="Blanco", codigo_hex="#FFFFFF")
        self.talla = Talla.objects.create(nombre="M")

        self.dummy_image = SimpleUploadedFile(
            "dummy.jpg", b"file_content", content_type="image/jpeg"
        )

        self.producto = Producto.objects.create(
            nombre="Playera Polo",
            descripcion="Playera cómoda",
            categoria=self.categoria,
            escuela=self.escuela,
            imagen_portada=self.dummy_image,
        )
        self.color_producto = ColorProducto.objects.create(
            producto=self.producto, color=self.color, imagen_color=self.dummy_image
        )
        self.variante = TallaVariante.objects.create(
            color_producto=self.color_producto,
            talla=self.talla,
            sku="POLO-BLA-M",
            stock=10,
            precio=Decimal("150.00"),
        )
        self.pedido = Pedido.objects.create(
            usuario=self.user, total=Decimal("150.00"), estado="pendiente"
        )
        self.detalle = DetallesPedido.objects.create(
            pedido=self.pedido,
            talla_variante=self.variante,
            cantidad=1,
            total=Decimal("150.00"),
        )
        self.favorito = Favoritos.objects.create(
            usuario=self.user, talla_variante=self.variante
        )
        self.historial = HistorialStock.objects.create(
            talla_variante=self.variante, cantidad_anterior=5, cantidad_nueva=10
        )

    def test_model_str_methods(self):
        self.assertEqual(str(self.categoria), "Uniformes")
        self.assertEqual(str(self.escuela), "Escuela Secundaria")
        self.assertEqual(str(self.color), "Blanco")
        self.assertEqual(str(self.talla), "M")
        self.assertEqual(str(self.producto), "Playera Polo")
        self.assertEqual(str(self.color_producto), "Playera Polo - Blanco")
        self.assertEqual(str(self.variante), "Playera Polo - Blanco - M")
        self.assertEqual(str(self.pedido), f"Pedido {self.pedido.id} de {self.user}")
        self.assertEqual(
            str(self.detalle),
            f"Detalle del Pedido {self.pedido.id} - {self.variante.sku}",
        )
        self.assertEqual(
            str(self.favorito),
            f"Favorito de {self.user} - {self.variante.sku}",
        )
        self.assertEqual(
            str(self.historial),
            f"Cambio de Stock: {self.variante.sku} ({self.historial.cantidad_anterior} -> {self.historial.cantidad_nueva})",
        )


class EcommerceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.categoria = Categoria.objects.create(nombre="Uniformes")
        self.escuela = Escuela.objects.create(nombre="Escuela Secundaria")
        self.color = Color.objects.create(nombre="Blanco", codigo_hex="#FFFFFF")
        self.talla = Talla.objects.create(nombre="M")

        self.dummy_image = SimpleUploadedFile(
            "dummy.jpg", b"file_content", content_type="image/jpeg"
        )

        self.producto = Producto.objects.create(
            nombre="Playera Polo",
            descripcion="Playera cómoda",
            categoria=self.categoria,
            escuela=self.escuela,
            imagen_portada=self.dummy_image,
        )
        self.color_producto = ColorProducto.objects.create(
            producto=self.producto, color=self.color, imagen_color=self.dummy_image
        )
        self.variante = TallaVariante.objects.create(
            color_producto=self.color_producto,
            talla=self.talla,
            sku="POLO-BLA-M",
            stock=10,
            precio=Decimal("150.00"),
        )

    def test_index_view(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_catalogo_view(self):
        response = self.client.get(reverse("catalogo"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalogo.html")

    def test_contacto_view(self):
        response = self.client.get(reverse("contacto"))
        self.assertEqual(response.status_code, 200)

    def test_toggle_favorito_unauthenticated(self):
        response = self.client.post(reverse("toggle-favorito", args=[self.variante.id]))
        self.assertEqual(response.status_code, 401)

    def test_toggle_favorito_authenticated_add_and_remove(self):
        self.client.login(username="testuser", password="password123")
        # Add
        response = self.client.post(reverse("toggle-favorito", args=[self.variante.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["estado"], "agregado")
        self.assertTrue(
            Favoritos.objects.filter(
                usuario=self.user, talla_variante=self.variante
            ).exists()
        )

        # Remove
        response = self.client.post(reverse("toggle-favorito", args=[self.variante.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["estado"], "eliminado")
        self.assertFalse(
            Favoritos.objects.filter(
                usuario=self.user, talla_variante=self.variante
            ).exists()
        )
