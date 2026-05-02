# usuarios/models.py

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    colonia = models.CharField(max_length=100, blank=True, null=True)
    calle = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    es_administrador = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def crear_o_actualizar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea el perfil de Usuario automáticamente al crear un User,
    y sincroniza el flag es_administrador si es staff/superuser.
    """
    usuario, _ = Usuario.objects.get_or_create(user=instance)

    # Si el usuario de Django es staff o superuser, marcamos es_administrador como True
    if instance.is_staff or instance.is_superuser:
        if not usuario.es_administrador:
            usuario.es_administrador = True
            usuario.save()
    elif usuario.es_administrador:
        # Opcional: si deja de ser staff, le quitamos el flag (sincronización total)
        # usuario.es_administrador = False
        # usuario.save()
        pass
