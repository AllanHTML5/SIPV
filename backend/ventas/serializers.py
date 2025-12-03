from rest_framework import serializers
from .models import CuentaPorCobrar, Abono


class CuentaPorCobrarSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    venta_numero = serializers.CharField(source="venta.numero", read_only=True)

    class Meta:
        model = CuentaPorCobrar
        fields = [
            "id",
            "cliente",
            "cliente_nombre",
            "venta",
            "venta_numero",
            "monto_total",
            "saldo_pendiente",
            "fecha_vencimiento",
            "created_at",
        ]


class AbonoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abono
        fields = "__all__"
