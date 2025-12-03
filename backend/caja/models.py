# caja/models.py
from django.db import models
from common.models import TimeStampedModel

class Caja(TimeStampedModel):
    fecha_apertura = models.DateTimeField()
    monto_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_cierre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    abierta = models.BooleanField(default=True)
