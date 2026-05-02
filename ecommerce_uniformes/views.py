import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Min, Max
from django.utils import timezone
from django.contrib import messages
from .models import (
    Producto,
    ColorProducto,
    TallaVariante,
    Favoritos,
    ItemCarrito,
    Pedido,
    DetallesPedido,
    Categoria,
    Talla,
    Escuela,
    MensajeContacto,
)
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from functools import wraps
from .models import ClicksWhatsapp
from django.conf import settings


def index(request):
    return render(request, "index.html")


def catalogo(request):
    # 1. Leer filtros desde GET
    escuela_ids = request.GET.getlist("escuelas")
    categoria_ids = request.GET.getlist("categorias")
    talla_ids = request.GET.getlist("tallas")
    disponibilidad = request.GET.getlist("disponibilidad")
    query = request.GET.get("q", "").strip()

    # 2. Queryset base de productos
    productos = Producto.objects.all()

    # Búsqueda por texto
    if query:
        productos = productos.filter(nombre__icontains=query)

    # 3. Filtrar por escuela y categoría
    if escuela_ids:
        productos = productos.filter(escuela__id__in=escuela_ids)
    if categoria_ids:
        productos = productos.filter(categoria__id__in=categoria_ids)

    # 4. Filtrar por tallas
    if talla_ids:
        productos = productos.filter(
            colores__tallas__talla__id__in=talla_ids
        ).distinct()

    # 5. Filtrar por disponibilidad (revertimos al método por suma de stocks)
    if disponibilidad:
        # obtenemos para cada producto la suma de stock de todas sus variantes
        agg_by_prod = TallaVariante.objects.values(
            "color_producto__producto_id"
        ).annotate(total=Sum("stock"))
        disponibles_ids = []
        for entry in agg_by_prod:
            pid = entry["color_producto__producto_id"]
            total = entry["total"] or 0
            if "disponible" in disponibilidad and total > 0:
                disponibles_ids.append(pid)
            if "agotado" in disponibilidad and total == 0:
                disponibles_ids.append(pid)
        productos = productos.filter(id__in=disponibles_ids)

    # 6. IDs de variantes favoritas y en carrito del usuario
    favoritos_ids = []
    carrito_ids = []
    if request.user.is_authenticated:
        favoritos_ids = list(
            Favoritos.objects.filter(usuario=request.user).values_list(
                "talla_variante_id", flat=True
            )
        )
        carrito_ids = list(
            ItemCarrito.objects.filter(usuario=request.user).values_list(
                "talla_variante_id", flat=True
            )
        )

    # 7. Construir lista final
    productos_con_datos = []
    for producto in productos.distinct():
        variantes = TallaVariante.objects.filter(color_producto__producto=producto)
        agregados = variantes.aggregate(
            total_stock=Sum("stock"), precio_min=Min("precio"), precio_max=Max("precio")
        )
        var_fav = variantes.filter(stock__gt=0).first() or variantes.first()

        variante_ids = set(variantes.values_list("id", flat=True))

        productos_con_datos.append(
            {
                "producto": producto,
                "total_stock": agregados["total_stock"] or 0,
                "precio_min": agregados["precio_min"] or 0,
                "precio_max": agregados["precio_max"] or 0,
                "en_favoritos": bool(variante_ids & set(favoritos_ids)),
                "en_carrito": bool(variante_ids & set(carrito_ids)),
                "variante_id": var_fav.id if var_fav else None,
            }
        )

    # 8. Render con contexto
    return render(
        request,
        "catalogo.html",
        {
            "productos_con_datos": productos_con_datos,
            "favoritos_ids": favoritos_ids,
            "carrito_ids": carrito_ids,
            "query": query,
            "escuelas": Escuela.objects.all(),
            "categorias": Categoria.objects.all(),
            "tallas": Talla.objects.all(),
            "escuelas_seleccionadas": escuela_ids,
            "categorias_seleccionadas": categoria_ids,
            "tallas_seleccionadas": talla_ids,
            "disponibilidad_seleccionada": disponibilidad,
        },
    )


def producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    colores = ColorProducto.objects.filter(producto=producto).select_related("color")

    # Crear un diccionario para pasar colores y tallas de manera ordenada
    color_tallas = {}
    variantes_data = []

    for color_producto in colores:
        tallas = TallaVariante.objects.filter(
            color_producto=color_producto
        ).select_related("talla")
        color_tallas[color_producto] = tallas

        # Construir lista de variantes
        for talla_variante in tallas:
            variantes_data.append(
                {
                    "color_id": color_producto.id,
                    "color_nombre": color_producto.color.nombre,
                    "talla_id": talla_variante.talla.id,
                    "talla_nombre": talla_variante.talla.nombre,
                    "sku": talla_variante.sku,
                    "precio": float(talla_variante.precio),
                    "stock": talla_variante.stock,
                    "imagen": (
                        color_producto.imagen_color.url
                        if color_producto.imagen_color
                        else ""
                    ),
                }
            )

    favoritos_ids = []
    carrito_items = {}
    if request.user.is_authenticated:
        favoritos_ids = list(
            Favoritos.objects.filter(usuario=request.user).values_list(
                "talla_variante_id", flat=True
            )
        )
        for item in ItemCarrito.objects.filter(
            usuario=request.user, talla_variante__color_producto__producto=producto
        ):
            carrito_items[item.talla_variante_id] = item.cantidad

    contexto = {
        "producto": producto,
        "colores": colores,
        "color_tallas": color_tallas,
        "variantes_json": json.dumps(variantes_data, cls=DjangoJSONEncoder),
        "favoritos_ids": favoritos_ids,
        "carrito_items_json": json.dumps(carrito_items),
    }

    return render(request, "producto.html", contexto)


@login_required
def favoritos(request):
    # Traer las variantes favoritas con todas las relaciones necesarias
    favoritos_qs = Favoritos.objects.filter(usuario=request.user).select_related(
        "talla_variante__color_producto__producto",
        "talla_variante__talla",
        "talla_variante__color_producto__color",
    )

    for f in favoritos_qs:
        f.total = f.cantidad * f.talla_variante.precio

    # En vez de solo variantes, pasa el queryset completo de Favoritos
    return render(
        request,
        "favoritos.html",
        {
            "favoritos": favoritos_qs,
        },
    )


def contacto(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")
        telefono = request.POST.get("telefono")
        mensaje = request.POST.get("comentario")

        from .models import MensajeContacto

        MensajeContacto.objects.create(
            nombre=nombre, email=email, telefono=telefono, mensaje=mensaje
        )
        messages.success(
            request,
            "¡Tu mensaje ha sido enviado correctamente! Nos pondremos en contacto contigo pronto.",
        )
        return redirect("contacto")

    return render(request, "contacto.html")


def login_required_json(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "No autenticado"}, status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped_view


@login_required_json
@require_POST
def toggle_favorito(request, variante_id):
    usuario = request.user
    try:
        variante = TallaVariante.objects.get(id=variante_id)
    except TallaVariante.DoesNotExist:
        return JsonResponse({"error": "Variante no encontrada"}, status=404)

    cantidad = request.POST.get("cantidad")
    try:
        cantidad = int(cantidad)
        if cantidad < 1:
            cantidad = 1
    except (TypeError, ValueError):
        cantidad = 1  # valor por defecto si no se proporciona cantidad válida

    favorito, creado = Favoritos.objects.get_or_create(
        usuario=usuario, talla_variante=variante
    )

    if not creado:
        favorito.delete()
        estado = "eliminado"
    else:
        favorito.cantidad = cantidad
        favorito.save()
        estado = "agregado"

    return JsonResponse({"estado": estado})


@login_required
@require_POST
def actualizar_cantidad_favorito(request, variante_id):
    cantidad = int(request.POST.get("cantidad", 1))
    if cantidad < 1:
        return JsonResponse({"error": "Cantidad inválida"}, status=400)

    try:
        favorito = Favoritos.objects.get(
            usuario=request.user, talla_variante_id=variante_id
        )
        favorito.cantidad = cantidad
        favorito.save()
        return JsonResponse({"estado": "ok", "cantidad": favorito.cantidad})
    except Favoritos.DoesNotExist:
        return JsonResponse({"estado": "no_agregado"})


# ───────────────────────── CARRITO ─────────────────────────


def _carrito_count(user):
    return ItemCarrito.objects.filter(usuario=user).count()


@login_required_json
@require_POST
def toggle_carrito_producto(request, producto_id):
    """Toggle de carrito a nivel de producto: quita TODAS las variantes o agrega la primera disponible."""
    producto = get_object_or_404(Producto, id=producto_id)
    variantes = TallaVariante.objects.filter(color_producto__producto=producto)
    items_en_carrito = ItemCarrito.objects.filter(
        usuario=request.user, talla_variante__in=variantes
    )

    if items_en_carrito.exists():
        items_en_carrito.delete()
        return JsonResponse(
            {"estado": "eliminado", "carrito_count": _carrito_count(request.user)}
        )

    primera = variantes.filter(stock__gt=0).first() or variantes.first()
    if primera:
        ItemCarrito.objects.get_or_create(
            usuario=request.user,
            talla_variante=primera,
            defaults={"cantidad": 1},
        )
        return JsonResponse(
            {"estado": "agregado", "carrito_count": _carrito_count(request.user)}
        )
    return JsonResponse({"error": "Sin variantes disponibles"}, status=400)


@login_required
def ver_carrito(request):
    items = ItemCarrito.objects.filter(usuario=request.user).select_related(
        "talla_variante__color_producto__producto",
        "talla_variante__talla",
        "talla_variante__color_producto__color",
    )
    total = sum(item.subtotal() for item in items)
    return render(request, "carrito.html", {"items": items, "total": total})


@login_required_json
@require_POST
def agregar_al_carrito(request, variante_id):
    variante = get_object_or_404(TallaVariante, id=variante_id)
    try:
        cantidad_a_sumar = max(1, int(request.POST.get("cantidad", 1)))
    except (TypeError, ValueError):
        cantidad_a_sumar = 1

    item, creado = ItemCarrito.objects.get_or_create(
        usuario=request.user,
        talla_variante=variante,
        defaults={"cantidad": cantidad_a_sumar},
    )

    if not creado:
        # Si ya existe, sumamos la cantidad (respetando el stock)
        nueva_cantidad = item.cantidad + cantidad_a_sumar
        if nueva_cantidad > variante.stock:
            nueva_cantidad = variante.stock
        item.cantidad = nueva_cantidad
        item.save()
        return JsonResponse(
            {
                "estado": "actualizado",
                "cantidad": item.cantidad,
                "carrito_count": _carrito_count(request.user),
            }
        )

    return JsonResponse(
        {
            "estado": "agregado",
            "cantidad": item.cantidad,
            "carrito_count": _carrito_count(request.user),
        }
    )


@login_required_json
@require_POST
def toggle_carrito(request, variante_id):
    variante = get_object_or_404(TallaVariante, id=variante_id)
    try:
        cantidad = max(1, int(request.POST.get("cantidad", 1)))
    except (TypeError, ValueError):
        cantidad = 1

    item, creado = ItemCarrito.objects.get_or_create(
        usuario=request.user,
        talla_variante=variante,
        defaults={"cantidad": cantidad},
    )
    if not creado:
        item.delete()
        return JsonResponse(
            {"estado": "eliminado", "carrito_count": _carrito_count(request.user)}
        )
    return JsonResponse(
        {"estado": "agregado", "carrito_count": _carrito_count(request.user)}
    )


@login_required
@require_POST
def actualizar_cantidad_carrito(request, variante_id):
    try:
        cantidad = int(request.POST.get("cantidad", 1))
        if cantidad < 1:
            return JsonResponse({"error": "Cantidad inválida"}, status=400)
        item = ItemCarrito.objects.get(
            usuario=request.user, talla_variante_id=variante_id
        )
        item.cantidad = cantidad
        item.save()
        return JsonResponse({"estado": "ok", "subtotal": str(item.subtotal())})
    except ItemCarrito.DoesNotExist:
        return JsonResponse({"error": "Item no encontrado"}, status=404)


@login_required
@require_POST
def eliminar_item_carrito(request, variante_id):
    ItemCarrito.objects.filter(
        usuario=request.user, talla_variante_id=variante_id
    ).delete()
    return JsonResponse(
        {"estado": "eliminado", "carrito_count": _carrito_count(request.user)}
    )


@login_required
@require_POST
def confirmar_pedido(request):
    items = ItemCarrito.objects.filter(usuario=request.user).select_related(
        "talla_variante"
    )
    if not items.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect("carrito")

    # Verificar que el perfil del usuario tenga los datos necesarios

    try:
        perfil = request.user.usuario
        campos_requeridos = [perfil.telefono, perfil.calle, perfil.ciudad]
        if not all(campos_requeridos):
            messages.warning(
                request,
                "Completa tu perfil (teléfono, calle y ciudad) antes de confirmar el pedido.",
            )
            return redirect("perfil")
    except Exception:
        messages.warning(request, "Completa tu perfil antes de confirmar el pedido.")
        return redirect("perfil")

    # Calcular total
    total = sum(item.subtotal() for item in items)

    # Crear pedido en estado pendiente (sin descontar stock — se confirma manualmente por admin)
    pedido = Pedido.objects.create(
        usuario=request.user, total=total, estado="pendiente"
    )
    for item in items:
        DetallesPedido.objects.create(
            pedido=pedido,
            talla_variante=item.talla_variante,
            cantidad=item.cantidad,
            total=item.subtotal(),
        )

    # Construir mensaje de WhatsApp
    if settings.DEBUG:
        numero_whatsapp = "526560000000"
    else:
        numero_whatsapp = settings.NUMERO_WHATSAPP
    lineas = [f"Hola, me gustaría hacer el siguiente pedido (#{pedido.id}):"]
    for item in items:
        v = item.talla_variante
        lineas.append(
            f"- {item.cantidad}x {v.color_producto.producto.nombre} ({v.color_producto.color.nombre}, talla {v.talla.nombre}) — ${v.precio} c/u"
        )
    lineas.append(f"Total estimado: ${total}")
    mensaje = "\n".join(lineas)

    # Vaciar el carrito
    items.delete()

    import urllib.parse

    wa_url = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(mensaje)}"

    return render(
        request, "pedido_confirmado.html", {"pedido": pedido, "wa_url": wa_url}
    )


@user_passes_test(lambda u: u.is_staff)
def dashboard(request):
    """Panel de administración personalizado para el dueño del negocio."""
    # Estadísticas generales
    hoy = timezone.now().date()
    pedidos_hoy = Pedido.objects.filter(fecha__date=hoy).count()
    pedidos_pendientes = Pedido.objects.filter(estado="pendiente").count()
    total_ventas = Pedido.objects.aggregate(total=Sum("total"))["total"] or 0

    # Alertas de stock bajo (menos de 5 unidades)
    stock_bajo = (
        TallaVariante.objects.filter(stock__lt=5)
        .select_related("color_producto__producto", "talla", "color_producto__color")
        .order_by("stock")
    )

    # Pedidos recientes
    pedidos_recientes = Pedido.objects.select_related("usuario").order_by("-fecha")[:10]

    # Mensajes de contacto recientes
    mensajes_recientes = MensajeContacto.objects.order_by("-fecha")[:5]
    mensajes_sin_leer = MensajeContacto.objects.filter(leido=False).count()

    contexto = {
        "pedidos_hoy": pedidos_hoy,
        "pedidos_pendientes": pedidos_pendientes,
        "total_ventas": total_ventas,
        "stock_bajo": stock_bajo,
        "pedidos_recientes": pedidos_recientes,
        "mensajes_recientes": mensajes_recientes,
        "mensajes_sin_leer": mensajes_sin_leer,
    }
    return render(request, "admin/dashboard.html", contexto)


@login_required_json
@require_POST
def registrar_click_whatsapp(request):
    """Registra analítica de cuando un usuario hace clic en el botón de WhatsApp."""
    if request.user.is_authenticated:
        ClicksWhatsapp.objects.create(usuario=request.user)
    return JsonResponse({"status": "ok"})
