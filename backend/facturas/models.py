from django.db import models
from django.contrib.auth.models import User
from maestros.models import Proveedor, Producto
from ventas.models import Cliente, Venta


class Factura(models.Model):
    TIPO_CHOICES = [
        ("VENTA", "Factura de Venta"),
        ("COMPRA", "Factura de Compra"),
    ]

    numero = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    # Enlace directo a la venta o compra
    venta = models.OneToOneField(
        Venta,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="factura_sipv"
    )

    # Venta → Cliente
    cliente = models.ForeignKey(
        Cliente, null=True, blank=True, on_delete=models.SET_NULL
    )

    # Compra → Proveedor
    proveedor = models.ForeignKey(
        Proveedor, null=True, blank=True, on_delete=models.SET_NULL
    )

    fecha = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    # Nuevos campos

    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ("EFECTIVO", "Efectivo"),
            ("TARJETA", "Tarjeta"),
            ("TRANSFERENCIA", "Transferencia"),
            ("CREDITO", "Crédito"),
        ],
        null=True,
        blank=True,
    )

    referencia_pago = models.CharField(max_length=100, null=True, blank=True)
    efectivo_recibido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cambio_entregado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Factura {self.numero} ({self.tipo})"


class FacturaDetalle(models.Model):
    factura = models.ForeignKey(Factura, related_name="detalles", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)

    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto} ({self.cantidad})"
