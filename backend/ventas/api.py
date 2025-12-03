from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import CuentaPorCobrar, Abono
from .serializers import CuentaPorCobrarSerializer, AbonoSerializer


class CuentaPorCobrarViewSet(viewsets.ModelViewSet):
    queryset = CuentaPorCobrar.objects.all()
    serializer_class = CuentaPorCobrarSerializer

    # GET /api/cuentas-por-cobrar/pendientes/
    @action(detail=False, methods=["get"])
    def pendientes(self, request):
        cuentas = CuentaPorCobrar.objects.filter(saldo_pendiente__gt=0)
        serializer = self.get_serializer(cuentas, many=True)
        return Response(serializer.data)

    # GET /api/cuentas-por-cobrar/vencidas/
    @action(detail=False, methods=["get"])
    def vencidas(self, request):
        from django.utils import timezone
        hoy = timezone.now().date()

        cuentas = CuentaPorCobrar.objects.filter(
            saldo_pendiente__gt=0,
            fecha_vencimiento__lt=hoy
        )
        serializer = self.get_serializer(cuentas, many=True)
        return Response(serializer.data)


class AbonoViewSet(viewsets.ModelViewSet):
    queryset = Abono.objects.all()
    serializer_class = AbonoSerializer

@action(detail=False, methods=["get"])
def reporte(self, request):
    from .reports import reporte_cartera
    return Response(reporte_cartera())
