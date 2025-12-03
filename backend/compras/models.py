# compras/models.py
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from common.models import TimeStampedModel
from maestros.models import Producto, Proveedor
from inventario.models import MovimientoInventario
from django.contrib.auth.models import User


ESTADOS = (
    ("BORRADOR", "BORRADOR"),
    ("CONFIRMADA", "CONFIRMADA"),
    ("ANULADA", "ANULADA"),
)



class Compra(TimeStampedModel):
    proveedor = models.ForeignKey(
        Proveedor,
	null=True,
	blank=True,
        on_delete=models.PROTECT,
        related_name="compra"
    )
    fecha = models.DateField(default=timezone.localdate)

    estado = models.CharField(
        max_length=12,
        choices=ESTADOS,
        default="BORRADOR"
    )

    tasa_impuesto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("15.00")
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    impuesto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    creado_por = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="compras_creadas"
    )

    procesada = models.BooleanField(default=False)

    def __str__(self):
        return f"Compra #{self.pk} ({self.estado})"

    def calcular_totales(self):
        """
        SOLO calcula (no guarda). Devuelve (subtotal, impuesto, total).
        """
        sub = Decimal("0.00")

        for d in self.detalles.all():
            sub += (d.cantidad or 0) * (d.costo_unitario or 0)

        sub = sub.quantize(Decimal("0.01"))
        imp = (sub * (self.tasa_impuesto or 0) / Decimal("100")).quantize(Decimal("0.01"))
        tot = (sub + imp).quantize(Decimal("0.01"))

        return sub, imp, tot


    @transaction.atomic
    def materializar_movimientos(self):
        """
        Crea ENTRADAS por cada detalle (idempotente).
        NO guarda self, no toca señales de Compra.
        """
        if self.estado != "CONFIRMADA":
            return
        for d in self.detalles.select_related("producto").all():
            ref = f"COMPRA:{self.pk}:{d.pk}"
            if MovimientoInventario.objects.filter(referencia=ref).exists():
                continue
            MovimientoInventario.objects.create(
                producto=d.producto,
                tipo="ENTRADA",
                cantidad=d.cantidad,
                costo_unitario=d.costo_unitario,
                referencia=ref,
                motivo=f"Compra #{self.pk}",
            )

class CompraDetalle(TimeStampedModel):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        verbose_name = "Detalle de compra"
        verbose_name_plural = "Detalles de compra"

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    def precio_unitario(self):
        return self.costo_unitario
