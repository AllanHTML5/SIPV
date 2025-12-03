from django.db import models
from django.conf import settings
from maestros.models import Producto, Proveedor
from common.models import TimeStampedModel
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
import re


class Cliente(TimeStampedModel):
    nombre = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    es_invitado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

    # PROPIEDAD: SALDO TOTAL
    @property
    def saldo_total(self):
        return sum(
            cc.saldo_pendiente
            for cc in self.cuentas_por_cobrar.all()
        )

    def clean(self):
        # VALIDACIÓN DEL NOMBRE
        patron_nombre = r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s#/\.\-_]+"

        if not re.fullmatch(patron_nombre, self.nombre):
            raise ValidationError({
                "nombre": "El nombre contiene caracteres no válidos."
            })

        # VALIDACIÓN DEL TELÉFONO
        if self.telefono:
            if not re.fullmatch(r"\d{8}", self.telefono):
                raise ValidationError({
                    "telefono": "El teléfono debe contener exactamente 8 dígitos."
                })

            if self.telefono[0] not in ["2", "3", "7", "8", "9"]:
                raise ValidationError({
                    "telefono": "El teléfono debe iniciar con 2, 3, 7, 8 o 9 (formato Honduras)."
                })

        super().clean()



class Venta(TimeStampedModel):
    CANAL = (
        ("POS", "Punto de venta"),
        ("WEB", "Web / tienda en línea"),
    )

    ESTADO = (
        ("BORRADOR", "Borrador"),
        ("PAGADA", "Pagada"),
        ("CANCELADA", "Cancelada"),
    )

    METODOS_PAGO = (
        ("EFECTIVO", "Efectivo"),
        ("TARJETA", "Tarjeta"),
        ("TRANSFERENCIA", "Transferencia"),
        ("CREDITO", "Crédito"),
    )

    numero = models.CharField(max_length=20, unique=True)

    factura = models.OneToOneField(
        'facturas.Factura',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='venta_rel'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_cliente"
    )

    cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ventas",
        null=True,
        blank=True,
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_creadas"
    )

    canal = models.CharField(max_length=10, choices=CANAL, default="POS")
    estado = models.CharField(max_length=10, choices=ESTADO, default="BORRADOR")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    descuento_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        default="EFECTIVO"
    )

    efectivo_recibido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cambio_entregado = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    referencia_pago = models.CharField(max_length=100, blank=True, null=True)
    codigo_recogida = models.CharField(max_length=12, blank=True)

    def __str__(self):
        return f"Venta {self.numero}"

    # CREAR CUENTA POR COBRAR AL GUARDAR VENTA
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si es nueva y es crédito → crear cuenta por cobrar
        if is_new and self.metodo_pago == "CREDITO":
            from .models import CuentaPorCobrar 
            if self.cliente:
                CuentaPorCobrar.objects.create(
                    cliente=self.cliente,
                    venta=self,
                    monto_total=self.total,
                    saldo_pendiente=self.total,
                    fecha_vencimiento=timezone.now().date() + timedelta(days=30)
                )


class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)

    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"


class CuentaPorCobrar(TimeStampedModel):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="cuentas_por_cobrar"
    )

    venta = models.OneToOneField(
        Venta,
        on_delete=models.CASCADE,
        related_name="cuenta_por_cobrar"
    )

    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField()

    def __str__(self):
        return f"CC {self.venta.numero} - {self.cliente.nombre}"


class Abono(TimeStampedModel):
    cuenta = models.ForeignKey(
        CuentaPorCobrar,
        on_delete=models.CASCADE,
        related_name="abonos"
    )

    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Abono {self.monto} a {self.cuenta}"

    def clean(self):

        if not self.cuenta_id:
            return

        #  No permitir abonos <= 0
        if self.monto is None or self.monto <= 0:
            raise ValidationError({
                "monto": "El abono debe ser mayor a 0."
            })

        # No permitir abonar si la cuenta ya está pagada
        if self.cuenta.saldo_pendiente <= 0:
            raise ValidationError({
                "monto": "Esta cuenta ya está pagada. No se pueden registrar más abonos."
            })

        #  No permitir abonos mayores al saldo pendiente
        if self.monto > self.cuenta.saldo_pendiente:
            raise ValidationError({
                "monto": "El abono no puede ser mayor al saldo pendiente."
            })

        super().clean()

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None

        super().save(*args, **kwargs)

        # Solo descontar si es un abono recién creado
        if es_nuevo:
            cuenta = self.cuenta

            # Descontar saldo
            cuenta.saldo_pendiente -= self.monto

            # Evitar que quede en negativo
            if cuenta.saldo_pendiente < 0:
                cuenta.saldo_pendiente = 0

            cuenta.save()
