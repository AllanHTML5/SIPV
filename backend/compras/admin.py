from django.contrib import admin
from django.db.models import Sum, F, DecimalField
from unfold.admin import ModelAdmin

from .models import Compra, CompraDetalle
from .forms import CompraForm, CompraDetalleForm, CompraDetalleFormSet



class CompraDetalleInline(admin.TabularInline):
    model = CompraDetalle
    form = CompraDetalleForm
    formset = CompraDetalleFormSet
    extra = 1

    autocomplete_fields = ("producto",)

    fields = ("producto", "cantidad", "costo_unitario", "subtotal_preview")
    readonly_fields = ("subtotal_preview",)

    def subtotal_preview(self, obj):
        if obj.pk:
            try:
                total = obj.cantidad * obj.costo_unitario
                return f"L {total:.2f}"
            except:
                return "-"
        return "-"
    subtotal_preview.short_description = "Subtotal"



@admin.register(Compra)
class CompraAdmin(ModelAdmin):
    form = CompraForm
    inlines = [CompraDetalleInline]


    list_display = ("id", "proveedor", "fecha", "estado", "total", "procesada")
    list_filter = ("estado", "fecha", "proveedor")
    search_fields = ("id", "proveedor__nombre")
    ordering = ("-fecha", "-id")

    readonly_fields = (
        "subtotal",
        "impuesto",
        "total",
        "creado",
        "actualizado",
    )


    fieldsets = (
        ("🧾 Datos de la compra", {
            "classes": ("card",),   
            "fields": ("proveedor", "fecha", "estado"),
        }),

        ("💰 Totales (automáticos)", {
            "classes": ("card",),
            "fields": ("subtotal", "impuesto", "total"),
        }),

        ("📌 Auditoría", {
            "classes": ("card",),
            "fields": ("creado", "actualizado"),
        }),
    )



    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        detalles = obj.detalles.all()
        if not detalles.exists():
            return

        subtotal = detalles.aggregate(
            total=Sum(
                F("cantidad") * F("costo_unitario"),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )["total"] or 0

        obj.subtotal = subtotal
        obj.impuesto = round(subtotal * obj.tasa_impuesto / 100, 2)
        obj.total = obj.subtotal + obj.impuesto
        obj.save()


    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for det in instances:
            if det.costo_unitario == 0 and det.producto:
                det.costo_unitario = det.producto.costo_promedio

            det.save()

        formset.save_m2m()

        compra = formset.instance
        detalles = compra.detalles.all()

        subtotal = detalles.aggregate(
            total=Sum(
                F("cantidad") * F("costo_unitario"),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )["total"] or 0

        compra.subtotal = subtotal
        compra.impuesto = round(subtotal * compra.tasa_impuesto / 100, 2)
        compra.total = compra.subtotal + compra.impuesto
        compra.save()


    @admin.display(boolean=True, description="Procesada")
    def procesada(self, obj):
        return obj.estado == "CONFIRMADA"
