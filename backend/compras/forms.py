# compras/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Compra, CompraDetalle
from django.utils import timezone


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ("proveedor", "fecha", "estado")
        widgets = {
            "proveedor": forms.Select(attrs={"class": "border rounded px-3 py-2 w-full"}),
            "fecha": forms.DateInput(
                attrs={"type": "date", "class": "border rounded px-3 py-2"}
            ),
            "estado": forms.Select(attrs={"class": "border rounded px-3 py-2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk and not self.initial.get("fecha"):
            self.initial["fecha"] = timezone.localdate()

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        if not fecha:
            return timezone.localdate()
        return fecha


class CompraDetalleForm(forms.ModelForm):
    class Meta:
        model = CompraDetalle
        fields = ("producto", "cantidad", "costo_unitario")
        widgets = {
            "producto": forms.Select(attrs={"class": "border rounded px-3 py-2 w-full"}),
            "cantidad": forms.NumberInput(attrs={
                "class": "border rounded px-3 py-2",
                "step": "1",
                "min": "1",
            }),
            "costo_unitario": forms.NumberInput(attrs={
                "class": "border rounded px-3 py-2",
                "step": "0.01",
                "min": "0",
            }),
        }
        labels = {
            "costo_unitario": "Costo unitario",
        }

    def clean_cantidad(self):
        v = self.cleaned_data.get("cantidad")
        if v is None or v <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que 0.")
        return int(v)

    def clean_costo_unitario(self):
        v = self.cleaned_data.get("costo_unitario")
        if v is None or v < 0:
            raise forms.ValidationError("El costo unitario no puede ser negativo.")
        return v




CompraDetalleFormSet = inlineformset_factory(
    parent_model=Compra,
    model=CompraDetalle,
    form=CompraDetalleForm,
    extra=1,         
    can_delete=True,
    min_num=1,
    validate_min=True,
)
