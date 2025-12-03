# compras/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Compra, CompraDetalle

def _recalcular_y_actualizar(compra: Compra):
    """
    Recalcula totales y los aplica con .update() para NO disparar señales.
    Si la compra está CONFIRMADA, materializa movimientos.
    """
    sub, imp, tot = compra.calcular_totales()
    Compra.objects.filter(pk=compra.pk).update(subtotal=sub, impuesto=imp, total=tot)
    if compra.estado == "CONFIRMADA":
        compra.materializar_movimientos()

@receiver(post_save, sender=CompraDetalle)
def recalc_on_detalle_save(sender, instance: CompraDetalle, created, **kwargs):
    _recalcular_y_actualizar(instance.compra)

@receiver(post_delete, sender=CompraDetalle)
def recalc_on_detalle_delete(sender, instance: CompraDetalle, **kwargs):
    _recalcular_y_actualizar(instance.compra)

@receiver(post_save, sender=Compra)
def on_compra_save(sender, instance: Compra, created, **kwargs):
    _recalcular_y_actualizar(instance)
