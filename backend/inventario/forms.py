# inventario/forms.py
from django import forms
from maestros.models import Producto
from .models import MovimientoInventario

TIPO_AJUSTE = [
    ("AJUSTE_POS", "Ajuste positivo (+)"),
    ("AJUSTE_NEG", "Ajuste negativo (−)"),
]

class AjusteInventarioForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True).order_by('nombre'),
        widget=forms.Select(attrs={'class': 'border rounded px-2 py-1 w-full'})
    )
    tipo = forms.ChoiceField(choices=TIPO_AJUSTE, widget=forms.Select(attrs={'class': 'border rounded px-2 py-1 w-full'}))
    cantidad = forms.DecimalField(min_value=0.001, decimal_places=3, max_digits=12, widget=forms.NumberInput(attrs={'class': 'border rounded px-2 py-1 w-full'}))
    motivo = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'border rounded px-2 py-1 w-full', 'rows': 2}))

    def save(self, usuario):
        cd = self.cleaned_data
        cantidad = abs(cd['cantidad'])  # siempre positiva
        return MovimientoInventario.objects.create(
            producto=cd['producto'],
            tipo=cd['tipo'],             # AJUSTE_POS | AJUSTE_NEG
            cantidad=cantidad,           # SIEMPRE positiva
            motivo=cd['motivo'],
            usuario=usuario if hasattr(usuario, 'id') else None
        )
