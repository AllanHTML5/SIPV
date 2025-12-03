# maestros/models.py
from django.db import models
from common.models import TimeStampedModel
from django.core.exceptions import ValidationError
import re
from decimal import Decimal



class Categoria(TimeStampedModel):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self): 
        return self.nombre

    def clean(self):
        # Validación del nombre (HN)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s#/\.\-_]+", self.nombre):
            raise ValidationError({"nombre": "El nombre contiene caracteres no válidos."})

        super().clean()

class Proveedor(TimeStampedModel):
    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=14, blank=True, null=True)  # HN
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)
    contacto = models.CharField(max_length=100, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self): return self.nombre

    def clean(self):
        # Validación RTN de Honduras (14 dígitos)
        if self.rtn:
            if not re.fullmatch(r"\d{14}", self.rtn):
                raise ValidationError({"rtn": "El RTN debe contener exactamente 14 dígitos."})

        # Teléfono de Honduras (exactamente 8 dígitos)
        if self.telefono:
            if not re.fullmatch(r"\d{8}", self.telefono):
                raise ValidationError({"telefono": "El teléfono debe contener 8 dígitos (formato Honduras)."})
    def clean(self):
        # Validación del nombre (HN)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s#/\.\-_]+", self.nombre):
            raise ValidationError({"nombre": "El nombre contiene caracteres no válidos."})

        super().clean()


class Producto(TimeStampedModel):
    codigo_barras = models.CharField(max_length=50, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=150)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="productos"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_promedio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    creado = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    impuesto = models.DecimalField(max_digits=4, decimal_places=2, default=0.15)

    def __str__(self):
        return self.nombre

    def clean(self):
        # Código de barras opcional, pero si viene debe ser numérico
        if self.codigo_barras:
            if not self.codigo_barras.isdigit():
                raise ValidationError({"codigo_barras": "El código de barras debe contener solo números."})
            if not (8 <= len(self.codigo_barras) <= 50):
                raise ValidationError({"codigo_barras": "El código de barras debe tener entre 8 y 50 dígitos."})

        # Precios y costos no negativos
        if self.precio_venta < 0:
            raise ValidationError({"precio_venta": "El precio de venta no puede ser negativo."})

        if self.costo_promedio < 0:
            raise ValidationError({"costo_promedio": "El costo promedio no puede ser negativo."})

        # Stock mínimo no negativo
        if self.stock_minimo < 0:
            raise ValidationError({"stock_minimo": "El stock mínimo no puede ser negativo."})

        # Impuesto permitido en Honduras (0% a 15%)

        if not (Decimal("0") <= self.impuesto <= Decimal("0.15")):
            raise ValidationError({"impuesto": "El impuesto debe estar entre 0.00 y 0.15 (15%)."})
        super().clean()

