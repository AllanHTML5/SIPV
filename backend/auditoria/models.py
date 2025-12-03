# auditoria/models.py
from django.db import models
from common.models import TimeStampedModel

class Bitacora(TimeStampedModel):
    usuario = models.CharField(max_length=150, blank=True)
    accion = models.CharField(max_length=50)   
    objeto = models.CharField(max_length=50)  
    objeto_id = models.CharField(max_length=50, blank=True)
    detalle = models.TextField(blank=True)
