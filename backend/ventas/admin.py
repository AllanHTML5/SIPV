# ventas/admin.py
from django.contrib import admin
from .models import Venta, Cliente
from .models import CuentaPorCobrar, Abono

#  ADMIN PARA CLIENTE
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "telefono", "es_invitado", "creado")
    search_fields = ("nombre", "email", "telefono")
    list_filter = ("es_invitado",)
    ordering = ("nombre",)



#  ADMIN PARA VENTA
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    """
    Admin moderno para Venta.
    Compatible con FacturaAdmin.autocomplete_fields
    y con Unfold.
    """

    # Columnas visibles
    list_display = (
        "numero",
        "cliente",
        "cajero",
        "estado",
        "total",
        "creado",
        "metodo_pago",
    )

    # Búsqueda
    search_fields = (
        "numero",
        "cliente__nombre",
        "cajero__username",
    )

    # Filtros
    list_filter = (
        "estado",
        "canal",
        "metodo_pago",
        "creado",
    )

    # Navegación por fecha
    date_hierarchy = "creado"

    # Orden por defecto
    ordering = ("-creado",)

    # Para autocompletados en FacturaAdmin
    autocomplete_fields = ("cliente", "cajero")

    # Mejor organización de los campos
    fieldsets = (
        ("Datos generales", {
            "fields": ("numero", "cliente", "cajero", "canal", "estado")
        }),
        ("Totales", {
            "fields": ("subtotal", "impuesto", "total", "descuento_total")
        }),
        ("Pago", {
            "fields": ("metodo_pago", "efectivo_recibido", "cambio_entregado", "referencia_pago")
        }),
        ("Auditoría", {
            "fields": ("creado_por", "creado", "actualizado")
        }),
    )

    # Campos solo lectura
    readonly_fields = ("creado", "actualizado", "creado_por")

    # Autoasignar quién creó la venta
    def save_model(self, request, obj, form, change):
        if not obj.creado_por:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)





@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "venta",
        "monto_total",
        "saldo_pendiente",
        "fecha_vencimiento",
        "estado_cuenta",
        "creado",         # ← CAMBIADO
    )

    list_filter = ("fecha_vencimiento",)
    search_fields = ("cliente__nombre", "venta__numero")

    readonly_fields = ("cliente", "venta", "monto_total", "saldo_pendiente")

    def estado_cuenta(self, obj):
        if obj.saldo_pendiente == 0:
            return "PAGADA"
        if obj.fecha_vencimiento < obj.creado.date():
            return "VENCIDA"
        return "VIGENTE"

    estado_cuenta.short_description = "Estado"


@admin.register(Abono)
class AbonoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cuenta",
        "monto",
        "fecha",
        "creado",      
    )

    list_filter = ("fecha",)
    search_fields = ("cuenta__cliente__nombre", "cuenta__venta__numero")

    readonly_fields = ("fecha",)