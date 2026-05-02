from django.contrib import admin
from .models import (
    Pedido,
    Producto,
    Favoritos,
    ItemCarrito,
    DetallesPedido,
    HistorialStock,
    ClicksWhatsapp,
    Categoria,
    Color,
    Talla,
    ColorProducto,
    TallaVariante,
    Escuela,
    MensajeContacto,
)


@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "telefono", "fecha", "leido")
    list_filter = ("leido", "fecha")
    search_fields = ("nombre", "email", "mensaje")


# Opciones para mostrar inlines de tallas dentro de un colorproducto
class TallaVarianteInline(admin.TabularInline):
    model = TallaVariante
    extra = 1


class ColorProductoInline(admin.TabularInline):
    model = ColorProducto
    extra = 1


class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "modelo", "categoria", "escuela")
    search_fields = ("nombre", "modelo")
    list_filter = ("categoria", "escuela")
    inlines = [
        ColorProductoInline
    ]  # Que puedas agregar colores desde Producto directamente


@admin.register(ColorProducto)
class ColorProductoAdmin(admin.ModelAdmin):
    list_display = ("producto", "color")
    inlines = [
        TallaVarianteInline
    ]  # Que puedas agregar tallas directamente dentro del colorproducto


@admin.register(TallaVariante)
class TallaVarianteAdmin(admin.ModelAdmin):
    list_display = ("color_producto", "talla", "sku", "stock", "precio")
    list_filter = ("color_producto__producto", "talla")
    search_fields = ("sku",)


# admin.site.register(Usuario)
admin.site.register(Pedido)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Escuela)
admin.site.register(Favoritos)
admin.site.register(DetallesPedido)
admin.site.register(HistorialStock)
admin.site.register(ClicksWhatsapp)
admin.site.register(Categoria)
admin.site.register(Color)
admin.site.register(Talla)
admin.site.register(ItemCarrito)
