from rest_framework import serializers
from .models import Categoria, Proveedor, Producto


# --------------------------------------
# CATEGORÍAS
# --------------------------------------
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = [
            "id",
            "nombre",
            "descripcion",
            "estado",
            "creado",
            "actualizado",
        ]
        read_only_fields = ["id", "creado", "actualizado"]


# --------------------------------------
# PROVEEDORES
# --------------------------------------
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = [
            "id",
            "nombre",
            "rtn",
            "direccion",
            "telefono",
            "email",
            "contacto",
            "estado",
            "creado",
            "actualizado",
        ]
        read_only_fields = ["id", "creado", "actualizado"]


# --------------------------------------
# PRODUCTOS
# --------------------------------------
class ProductoSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(
        source="proveedor.nombre", read_only=True
    )
    categoria_nombre = serializers.CharField(
        source="categoria.nombre", read_only=True
    )

    class Meta:
        model = Producto
        fields = [
            "id",
            "codigo_barras",
            "nombre",
            "imagen",
            "proveedor",
            "proveedor_nombre",
            "categoria",
            "categoria_nombre",
            "precio_venta",
            "costo_promedio",
            "stock_minimo",
            "activo",
            "impuesto",
            "creado",
            "actualizado",
        ]
        read_only_fields = ["id", "creado", "actualizado"]
