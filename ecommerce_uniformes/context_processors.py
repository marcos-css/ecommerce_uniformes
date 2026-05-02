from .models import ItemCarrito
from django.conf import settings

def carrito_count(request):
    """Inyecta el conteo de items del carrito en todos los templates."""
    if request.user.is_authenticated:
        count = ItemCarrito.objects.filter(usuario=request.user).count()
    else:
        count = 0
    return {"carrito_count": count}

def debug_mode(request):
    """Inyecta el valor de DEBUG en todos los templates."""
    return {"debug": settings.DEBUG}

def numero_whatsapp(request):
    """Inyecta el valor de NUMERO_WHATSAPP en todos los templates."""
    return {"numero_whatsapp": settings.NUMERO_WHATSAPP}