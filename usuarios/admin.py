# usuarios/admin.py
from django.contrib import admin
from .models import Usuario


class UsuarioAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "colonia",
        "calle",
        "ciudad",
        "estado",
        "codigo_postal",
        "telefono",
        "es_administrador",
    ]
    search_fields = ["user__username", "user__email"]


admin.site.register(Usuario, UsuarioAdmin)
