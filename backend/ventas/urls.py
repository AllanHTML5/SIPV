# ventas/urls.py
from django.urls import path
from . import views
from ventas.api import CuentaPorCobrarViewSet, AbonoViewSet
from rest_framework import routers
from django.urls import path, include


app_name = "ventas"
router = routers.DefaultRouter()
router.register(r'cuentas-por-cobrar', CuentaPorCobrarViewSet)
router.register(r'abonos', AbonoViewSet)

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/buscar-productos/", views.api_buscar_productos, name="api_buscar_productos"),
    path("api/finalizar/", views.api_finalizar_venta, name="api_finalizar"),
    path("api/todos/", views.api_todos_productos, name="api_todos"),
    path("crear/", views.crear_orden, name="crear_orden"),
    path("detalle/<int:pk>/", views.detalle, name="detalle"),
    path("api/detalle/<int:pk>/completar/", views.api_completar_venta, name="api_completar"),
    path("api/linea/agregar/", views.api_linea_agregar, name="linea_agregar"),
    path("api/linea/actualizar/", views.api_linea_actualizar, name="linea_actualizar"),
    path("api/linea/eliminar/", views.api_linea_eliminar, name="linea_eliminar"),
    path("api/recientes/", views.ventas_recientes_api, name="ventas_recientes_api"),
    path("api/lineas/<int:venta_id>/", views.api_lineas, name="api_lineas"),
    path("api/detalle/<int:pk>/cancelar/", views.api_cancelar_orden, name="api_cancelar"),
    path("api/detalle/<int:pk>/anular/", views.api_anular_orden, name="api_anular"),
    path("api/cliente-info/<int:cliente_id>/", views.api_cliente_info, name="api_cliente_info"),
    path("api/buscar-clientes/", views.api_buscar_clientes, name="api_buscar_clientes"),
    path("api/v1/", include(router.urls)),
    
    path("cartera/", views.cartera_dashboard, name="cartera_dashboard"),
    path("cartera/pendientes/", views.cartera_pendientes, name="cartera_pendientes"),
    path("cartera/vencidas/", views.cartera_vencidas, name="cartera_vencidas"),

    path("cartera/<int:pk>/", views.cartera_detalle, name="cartera_detalle"),
    path("cartera/<int:pk>/abonos/", views.abonos_list, name="abonos_list"),
    path("cartera/<int:pk>/abonos/nuevo/", views.abono_create, name="abono_create"),
    path("cliente/<int:cliente_id>/credito/", views.detalle_credito_cliente, name="detalle_credito_cliente"),

]
