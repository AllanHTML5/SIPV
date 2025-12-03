from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Venta, CuentaPorCobrar

@receiver(post_save, sender=Venta)
def crear_cuenta_por_cobrar(sender, instance, created, **kwargs):

    # Si NO es crédito: no hacemos nada
    if instance.metodo_pago != "CREDITO":
        print("⚠️ No es crédito, no se crea cuenta.")
        return

    # Si ya existe la cuenta, no duplicamos
    if hasattr(instance, "cuenta_por_cobrar"):
        print("⚠️ La venta ya tiene cuenta por cobrar, no se crea otra.")
        return

    # En este punto: es crédito y NO tiene cuenta → la creamos SIEMPRE
    CuentaPorCobrar.objects.create(
        cliente=instance.cliente,
        venta=instance,
        monto_total=instance.total,
        saldo_pendiente=instance.total,
        fecha_vencimiento=timezone.now().date() + timezone.timedelta(days=30)
    )

    print("CuentaPorCobrar creada para venta:", instance.numero)
