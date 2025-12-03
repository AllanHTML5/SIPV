# facturas/admin.py
from django.contrib import admin
from django import forms
from .models import Factura, FacturaDetalle
from maestros.models import Producto


# INLINE FORM

class FacturaDetalleInlineForm(forms.ModelForm):
    class Meta:
        model = FacturaDetalle
        fields = "__all__"

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get("precio_unitario")
        if precio in (None, ""):
            return 0
        return precio



# INLINE

class FacturaDetalleInline(admin.TabularInline):
    model = FacturaDetalle
    form = FacturaDetalleInlineForm
    extra = 1
    autocomplete_fields = ("producto",)

    fields = (
        "producto",
        "cantidad",
        "precio_unitario",
        "subtotal",
        "impuesto",
        "total",
    )

    readonly_fields = ("subtotal", "impuesto", "total")

# ADMIN PRINCIPAL

def generar_num_factura():
    ultimo = Factura.objects.order_by("-id").first()
    numero = 1 if not ultimo else ultimo.id + 1
    return f"FV-{numero:06d}"


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):

    readonly_fields = ("numero", "fecha", "subtotal", "impuesto", "total")
    autocomplete_fields = ("cliente", "proveedor", "venta")

    fieldsets = (
        ("Datos generales", {
            "fields": ("numero", "tipo", "venta", "cliente", "proveedor", "fecha", "creado_por")
        }),
        ("Totales", {
            "fields": ("subtotal", "impuesto", "total")
        }),
        ("Pago", {
            "fields": ("metodo_pago", "referencia_pago", "efectivo_recibido", "cambio_entregado")
        }),
        ("Notas", {
            "fields": ("notas",)
        })
    )

    inlines = [FacturaDetalleInline]

    def save_model(self, request, obj, form, change):
        if not obj.numero or obj.numero == "":
            obj.numero = generar_num_factura()

        if not obj.creado_por:
            obj.creado_por = request.user

        super().save_model(request, obj, form, change)

    class Media:
        js = ("admin/js/factura_dynamic.js",)
        css = {"all": ("admin/css/factura_dynamic.css",)}
