# inventario/models.py
from django.db import models, transaction
from maestros.models import Producto
from common.models import TimeStampedModel
from django.utils import timezone
from django.contrib.auth.models import User


class MovimientoInventario(TimeStampedModel):
    TIPO = (
        ("ENTRADA","ENTRADA"),
        ("SALIDA","SALIDA"),
        ("AJUSTE_POS","AJUSTE_POS"),
        ("AJUSTE_NEG","AJUSTE_NEG"),
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=12, choices=TIPO)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    referencia = models.CharField(max_length=30, blank=True)
    motivo = models.CharField(max_length=120, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        indexes = [models.Index(fields=["producto","creado"])]

class Existencia(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name='existencia')
    cantidad = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    actualizado = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "inventario_existencia"
        verbose_name = "Existencia"
        verbose_name_plural = "Existencias"

    def __str__(self):
        return f"{self.producto.nombre} → {self.cantidad}"
