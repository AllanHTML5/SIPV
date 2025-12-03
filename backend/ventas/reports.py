from django.db.models import Sum
from django.utils import timezone
from .models import CuentaPorCobrar


def reporte_cartera():
    hoy = timezone.now().date()

    vigente = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0,
        fecha_vencimiento__gte=hoy
    ).aggregate(total=Sum("saldo_pendiente"))["total"] or 0

    vencida = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0,
        fecha_vencimiento__lt=hoy
    ).aggregate(total=Sum("saldo_pendiente"))["total"] or 0

    total = vigente + vencida

    return {
        "vigente": vigente,
        "vencida": vencida,
        "total": total
    }
