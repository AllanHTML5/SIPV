from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Case, When, F, Value, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from decimal import Decimal

from .models import MovimientoInventario, Existencia

def _tabla_existe(nombre):
    # Evita query que cause error si no hay tablas aún
    try:
        with connection.cursor() as cursor:
            tablas = connection.introspection.table_names()
        return nombre in tablas
    except Exception:
        return False

DEC_QTY = DecimalField(max_digits=14, decimal_places=3)

def actualizar_existencia(sender, instance, created, **kwargs):
    p = instance.producto
    signed_qty = Case(
        When(tipo__in=['ENTRADA','AJUSTE_POS'], then=F('cantidad')),
        When(tipo__in=['SALIDA','AJUSTE_NEG'],  then=ExpressionWrapper(-F('cantidad'), output_field=DEC_QTY)),
        default=Value(0),
        output_field=DEC_QTY,
    )
    total = MovimientoInventario.objects.filter(producto=p).aggregate(
        s=Coalesce(Sum(signed_qty), Value(0, output_field=DEC_QTY), output_field=DEC_QTY)
    )['s']

    ex, _ = Existencia.objects.get_or_create(producto=p)
    ex.cantidad = total
    ex.save(update_fields=['cantidad','actualizado'])

def _recalcular_existencia(producto_id: int):
    """Suma todos los movimientos del producto en una forma robusta."""
    total = Decimal("0")
    movs = MovimientoInventario.objects.filter(producto_id=producto_id).values("tipo", "cantidad")
    for m in movs:
        tipo = m["tipo"]
        cant = Decimal(m["cantidad"])
        # Entradas suman, salidas restan 
        if tipo in ("ENTRADA", "AJUSTE_POS"):
            total += abs(cant)
        else:  
            total -= abs(cant)
    ex, _ = Existencia.objects.get_or_create(producto_id=producto_id)
    ex.cantidad = total
    ex.save(update_fields=["cantidad", "actualizado"])

@receiver(post_save, sender=MovimientoInventario)
def on_mov_guardado(sender, instance, **kwargs):
    _recalcular_existencia(instance.producto_id)

@receiver(post_delete, sender=MovimientoInventario)
def on_mov_borrado(sender, instance, **kwargs):
    _recalcular_existencia(instance.producto_id)
