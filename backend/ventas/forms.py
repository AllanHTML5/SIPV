from django import forms
from .models import Abono

class AbonoForm(forms.ModelForm):
    class Meta:
        model = Abono
        fields = ["monto"]
        widgets = {
            "monto": forms.NumberInput(attrs={
                "class": "form-input border rounded px-3 py-2 w-full"
            })
        }
