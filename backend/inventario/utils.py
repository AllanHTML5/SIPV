from django.db.models import F, Value, DecimalField
from django.db.models.functions import Coalesce

def annotate_stock(qs):
    return qs.annotate(
        stock=Coalesce(
            F("existencia__cantidad"),
            Value(0, output_field=DecimalField(max_digits=14, decimal_places=3)),
        )
    )
