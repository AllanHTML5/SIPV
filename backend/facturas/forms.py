from django import forms
from .models import FacturaDetalle


class FacturaDetalleForm(forms.ModelForm):
    """
    El precio_unitario no será requerido.
    Si viene vacío, se rellenará con el precio_venta del producto.
    """

    class Meta:
        model = FacturaDetalle
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        precio_unitario = cleaned.get("precio_unitario")

        # Si no ingresaron precio, usar el precio del producto
        if producto and (precio_unitario is None or precio_unitario == ""):
            cleaned["precio_unitario"] = producto.precio_venta

        return cleaned
