from django import forms
from .models import Usuario
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["telefono", "colonia", "calle", "ciudad", "estado", "codigo_postal"]
        widgets = {
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "656-000-0000",
                }
            ),
            "colonia": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actualiza tu colonia",
                }
            ),
            "calle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actualiza tu calle",
                }
            ),
            "ciudad": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actualiza tu ciudad",
                }
            ),
            "estado": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actualiza tu estado",
                }
            ),
            "codigo_postal": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actualiza tu código postal",
                }
            ),
        }


class NombreApellidoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Apellido",
                }
            ),
        }


class RegistroForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contraseña",
                "minlength": "8",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirmar contraseña",
                "minlength": "8",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre de usuario"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Correo electrónico"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Apellido"}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2:
            if password != password2:
                raise ValidationError("Las contraseñas no coinciden.")
            else:
                from django.contrib.auth.password_validation import validate_password

                try:
                    user = User(
                        username=cleaned_data.get("username"),
                        email=cleaned_data.get("email"),
                    )
                    validate_password(password, user)
                except ValidationError as e:
                    self.add_error("password", e)

        return cleaned_data
