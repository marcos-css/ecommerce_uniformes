from django.db import models
from django.conf import settings


class Pedido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=50,
        choices=[
            ("pendiente", "Pendiente"),
            ("enviado", "Enviado"),
            ("entregado", "Entregado"),
            ("cancelado", "Cancelado"),
        ],
    )

    def __str__(self):
        return f"Pedido {self.id} de {self.usuario}"


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen_portada = models.ImageField(upload_to="productos/")
    modelo = models.CharField(max_length=50, blank=True, null=True)
    categoria = models.ForeignKey("Categoria", on_delete=models.SET_NULL, null=True)
    escuela = models.ForeignKey("Escuela", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.nombre


class Color(models.Model):
    nombre = models.CharField(max_length=50)
    codigo_hex = models.CharField(
        max_length=7
    )  # Para guardar el color en HEX (#000000)

    def __str__(self):
        return self.nombre


class Escuela(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Talla(models.Model):
    nombre = models.CharField(max_length=10)  # XS, S, M, L, etc.

    def __str__(self):
        return self.nombre


class ColorProducto(models.Model):
    producto = models.ForeignKey(
        Producto, related_name="colores", on_delete=models.CASCADE
    )
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    imagen_color = models.ImageField(upload_to="productos/colores/")

    def __str__(self):
        return f"{self.producto.nombre} - {self.color.nombre}"


class TallaVariante(models.Model):
    color_producto = models.ForeignKey(
        ColorProducto, related_name="tallas", on_delete=models.CASCADE
    )
    talla = models.ForeignKey(Talla, on_delete=models.CASCADE)
    sku = models.CharField(max_length=50, unique=True)
    stock = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.color_producto} - {self.talla.nombre}"


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


class Favoritos(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    talla_variante = models.ForeignKey(
        TallaVariante, on_delete=models.CASCADE, null=True
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Favorito de {self.usuario} - {self.talla_variante}"


class DetallesPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    talla_variante = models.ForeignKey(TallaVariante, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle del Pedido {self.pedido.id} - {self.talla_variante}"


class HistorialStock(models.Model):
    talla_variante = models.ForeignKey(TallaVariante, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad_anterior = models.PositiveIntegerField()
    cantidad_nueva = models.PositiveIntegerField()

    def __str__(self):
        return f"Cambio de Stock: {self.talla_variante} ({self.cantidad_anterior} -> {self.cantidad_nueva})"


class ClicksWhatsapp(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)


class ItemCarrito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carrito",
    )
    talla_variante = models.ForeignKey(TallaVariante, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "talla_variante")

    def subtotal(self):
        return self.talla_variante.precio * self.cantidad

    def __str__(self):
        return f"Carrito de {self.usuario} - {self.talla_variante} x{self.cantidad}"


class MensajeContacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje de {self.nombre} ({self.fecha.strftime('%d/%m/%Y')})"
