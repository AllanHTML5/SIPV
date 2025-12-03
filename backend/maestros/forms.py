from django import forms
from .models import Categoria, Producto, Proveedor
import re
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from ventas.models import Cliente

# ============================================
# HELPERS
# ============================================

def normalize_numeric(val):
    if val is None:
        return val
    return str(val).replace(",", ".").strip()


def validate_decimal(field_name, value, min_value=0, max_decimals=None):
    value = normalize_numeric(value)

    try:
        num = float(value)
    except:
        raise forms.ValidationError(f"El campo {field_name} debe ser un número válido.")

    if num < min_value:
        raise forms.ValidationError(f"El campo {field_name} no puede ser negativo.")

    if max_decimals is not None and "." in value:
        dec = value.split(".")[1]
        if len(dec) > max_decimals:
            raise forms.ValidationError(
                f"Asegúrese de que no haya más de {max_decimals} dígitos decimales."
            )

    return num


def validate_text(field_name, value, min_length=3):
    if not value or len(value.strip()) < min_length:
        raise forms.ValidationError(
            f"El campo {field_name} debe tener al menos {min_length} caracteres."
        )

    if re.fullmatch(r"\d+", value.strip()):
        raise forms.ValidationError(f"El campo {field_name} no puede contener solo números.")

    return value.strip()


def validate_numeric_code(field_name, value, digits):
    if not value:
        return ""

    value = value.replace(" ", "")

    if not re.fullmatch(rf"\d{{{digits}}}", value):
        raise forms.ValidationError(
            f"El campo {field_name} debe tener exactamente {digits} dígitos numéricos."
        )

    return value


# ============================================
# FUNCIÓN DE WIDGET GLOBAL
# ============================================

WIDGET_INPUT = {
    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 "
             "focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm"
}

WIDGET_SELECT = {
    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg bg-white "
             "focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
}

WIDGET_CHECKBOX = {
    "class": "h-5 w-5 text-blue-600 rounded"
}


# ============================================
# FORMULARIOS
# ============================================

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "estado"]
        widgets = {
            "nombre": forms.TextInput(attrs=WIDGET_INPUT),
            "descripcion": forms.TextInput(attrs=WIDGET_INPUT),
            "estado": forms.CheckboxInput(attrs=WIDGET_CHECKBOX),
        }


class ProductoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.initial["impuesto"] = round((self.instance.impuesto or 0) * 100, 2)
        else:
            self.initial["impuesto"] = 15

    class Meta:
        model = Producto
        fields = [
            "codigo_barras",
            "nombre",
            "imagen",
            "proveedor",
            "categoria",
            "precio_venta",
            "costo_promedio",
            "stock_minimo",
            "activo",
            "impuesto",
        ]
        widgets = {
            "codigo_barras": forms.TextInput(attrs=WIDGET_INPUT),
            "nombre": forms.TextInput(attrs=WIDGET_INPUT),
            "imagen": forms.FileInput(attrs={"class": "block w-full text-sm text-slate-600"}),
            "proveedor": forms.Select(attrs=WIDGET_SELECT),
            "categoria": forms.Select(attrs=WIDGET_SELECT),
            "precio_venta": forms.NumberInput(attrs=WIDGET_INPUT),
            "costo_promedio": forms.NumberInput(attrs=WIDGET_INPUT),
            "stock_minimo": forms.NumberInput(attrs=WIDGET_INPUT),
            "activo": forms.CheckboxInput(attrs=WIDGET_CHECKBOX),
            "impuesto": forms.NumberInput(attrs=WIDGET_INPUT),
        }


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            "nombre",
            "rtn",
            "direccion",
            "telefono",
            "email",
            "contacto",
            "estado",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs=WIDGET_INPUT),
            "rtn": forms.TextInput(attrs=WIDGET_INPUT),
            "direccion": forms.TextInput(attrs=WIDGET_INPUT),
            "telefono": forms.TextInput(attrs=WIDGET_INPUT),
            "email": forms.EmailInput(attrs=WIDGET_INPUT),
            "contacto": forms.TextInput(attrs=WIDGET_INPUT),
            "estado": forms.CheckboxInput(attrs=WIDGET_CHECKBOX),
        }


class ClienteForm(forms.ModelForm):

    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre", "").strip()
        patron = r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s#/\.\-_]+"

        if not re.fullmatch(patron, nombre):
            raise forms.ValidationError("El nombre contiene caracteres no válidos.")

        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")

        return nombre

    def clean_telefono(self):
        tel = self.cleaned_data.get("telefono", "").strip()
        if not tel:
            return tel

        if not re.fullmatch(r"\d{8}", tel):
            raise forms.ValidationError("El teléfono debe tener 8 dígitos.")

        if tel[0] not in ["2", "3", "7", "8", "9"]:
            raise forms.ValidationError("El número debe iniciar con 2,3,7,8 o 9.")

        return tel

    class Meta:
        model = Cliente
        fields = ["nombre", "email", "telefono", "es_invitado"]
        widgets = {
            "nombre": forms.TextInput(attrs=WIDGET_INPUT),
            "email": forms.EmailInput(attrs=WIDGET_INPUT),
            "telefono": forms.TextInput(attrs=WIDGET_INPUT),
            "es_invitado": forms.CheckboxInput(attrs=WIDGET_CHECKBOX),
        }

