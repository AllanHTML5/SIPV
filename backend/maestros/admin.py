# maestros/admin.py
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Categoria, Proveedor, Producto

@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    list_display = ("id","nombre","estado","creado")
    list_filter = ("estado",)
    search_fields = ("nombre",)

@admin.register(Proveedor)
class ProveedorAdmin(ModelAdmin):
    list_display = ("id","nombre","rtn","telefono","estado","creado")
    search_fields = ("nombre","rtn")
    list_filter = ("estado",)

@admin.register(Producto)
class ProductoAdmin(ModelAdmin):
    list_display = ("id","nombre","codigo_barras","precio_venta","stock_minimo","activo","creado")
    list_filter = ("activo","categoria")
    search_fields = ("nombre","codigo_barras")
