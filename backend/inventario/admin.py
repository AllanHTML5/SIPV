# inventario/admin.py
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import MovimientoInventario

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(ModelAdmin):
    list_display = ("id","producto","tipo","cantidad","costo_unitario","creado")
    list_filter = ("tipo","producto")
    readonly_fields = ("producto","tipo","cantidad","costo_unitario","referencia","motivo","creado")
    def has_add_permission(self, *a, **kw): return False
    def has_delete_permission(self, *a, **kw): return False
