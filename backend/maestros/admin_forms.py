from django import forms
from .models import Producto


class ProductoAdminForm(forms.ModelForm):

    def clean_impuesto(self):
        raw = str(self.cleaned_data.get("impuesto")).replace(",", ".").strip()

        if raw == "":
            return 0

        try:
            valor = float(raw)
        except:
            raise forms.ValidationError("Ingrese un número válido para el impuesto.")

        # Si el usuario pone 15 → guardar 0.15
        if valor > 1:
            valor = valor / 100

        # Validación del modelo
        if not (0 <= valor <= 0.15):
            raise forms.ValidationError("El impuesto debe estar entre 0% y 15%.")

        return valor

    class Meta:
        model = Producto
        fields = "__all__"
