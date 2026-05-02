from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("usuarios/", include("usuarios.urls")),
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("favoritos/", views.favoritos, name="favoritos"),
    path("producto/<int:id>", views.producto, name="producto"),
    path("contacto/", views.contacto, name="contacto"),
    path(
        "toggle-favorito/<int:variante_id>/",
        views.toggle_favorito,
        name="toggle-favorito",
    ),
    path(
        "actualizar-cantidad-favorito/<int:variante_id>/",
        views.actualizar_cantidad_favorito,
        name="actualizar_cantidad_favorito",
    ),
    # Carrito
    path("carrito/", views.ver_carrito, name="carrito"),
    path(
        "carrito/agregar/<int:variante_id>/",
        views.agregar_al_carrito,
        name="agregar-carrito",
    ),
    path(
        "carrito/toggle/<int:variante_id>/", views.toggle_carrito, name="toggle-carrito"
    ),
    path(
        "carrito/toggle-producto/<int:producto_id>/",
        views.toggle_carrito_producto,
        name="toggle-carrito-producto",
    ),
    path(
        "carrito/actualizar/<int:variante_id>/",
        views.actualizar_cantidad_carrito,
        name="actualizar_carrito",
    ),
    path(
        "carrito/eliminar/<int:variante_id>/",
        views.eliminar_item_carrito,
        name="eliminar_item_carrito",
    ),
    path("carrito/confirmar/", views.confirmar_pedido, name="confirmar_pedido"),
    path(
        "click-whatsapp/",
        views.registrar_click_whatsapp,
        name="registrar-click-whatsapp",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
