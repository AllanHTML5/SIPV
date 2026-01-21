from django import forms
from django.contrib.auth.models import User, Group, Permission
import re



# VALIDACIONES GENERALES


def validate_text(field, value, min_length=2):
    if not value or len(value.strip()) < min_length:
        raise forms.ValidationError(f"El campo {field} debe tener al menos {min_length} caracteres.")
    if re.fullmatch(r"\d+", value):
        raise forms.ValidationError(f"El campo {field} no puede contener solo números.")
    return value.strip()


def validate_email(value):
    if value and "@" not in value:
        raise forms.ValidationError("Debe ingresar un correo válido.")
    return value



# FORMULARIO USUARIO


class UsuarioForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.CharField(required=False)

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-multiselect"})
    )

    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-multiselect"})
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        ]


    def clean_username(self):
        val = self.cleaned_data.get("username", "").strip()
        if len(val) < 4:
            raise forms.ValidationError("El nombre de usuario debe tener mínimo 4 caracteres.")
        return val

    def clean_first_name(self):
        return validate_text("nombre", self.cleaned_data.get("first_name", ""))

    def clean_last_name(self):
        return validate_text("apellido", self.cleaned_data.get("last_name", ""))

    def clean_email(self):
        return validate_email(self.cleaned_data.get("email", ""))



# FORMULARIO CAMBIO DE PASSWORD


class PasswordChangeForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        min_length=8,
        required=True
    )

    def clean_password(self):
        pwd = self.cleaned_data["password"]
        if len(pwd) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return pwd



# FORMULARIO GRUPOS

class GrupoForm(forms.ModelForm):
    permisos_asignados = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "w-full h-72 border rounded-lg p-2"
        })
    )

    permisos_disponibles = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "w-full h-72 border rounded-lg p-2"
        })
    )

    class Meta:
        model = Group
        fields = ["name"] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si estamos editando un grupo existente
        if self.instance.pk:
            asignados = self.instance.permissions.all()
            no_asignados = Permission.objects.exclude(id__in=asignados)
        else:
            asignados = Permission.objects.none()
            no_asignados = Permission.objects.all()

        # Asignar querysets
        self.fields["permisos_asignados"].queryset = asignados
        self.fields["permisos_disponibles"].queryset = no_asignados

    def save(self, commit=True):
        group = super().save(commit=False)

        if commit:
            group.save()
            group.permissions.clear()

            permisos_finales = self.cleaned_data["permisos_asignados"]

            for p in permisos_finales:
                group.permissions.add(p)

        return group
