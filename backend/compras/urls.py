from django.urls import path
from . import views

app_name = "compras"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard-data/", views.dashboard_data, name="dashboard_data"),

    # Crear compra tipo POS
    path("crear/", views.crear_compra_borrador, name="crear_compra_borrador"),

    # Pantalla POS detalle
    path("detalle/<int:pk>/", views.detalle_pos_compra, name="detalle"),
    path("detalle-pos/<int:pk>/", views.detalle_pos_compra, name="detalle_pos_compra"),

    # APIs
    path("api/buscar-productos/", views.api_buscar_productos, name="api_buscar_productos"),
    path("api/lineas/<int:pk>/", views.api_cargar_lineas, name="api_cargar_lineas"),
    path("api/agregar-linea/", views.api_agregar_linea, name="api_agregar_linea"),
    path("api/actualizar-linea/", views.api_actualizar_linea, name="api_actualizar_linea"),
    path("api/eliminar-linea/", views.api_eliminar_linea, name="api_eliminar_linea"),

    # Confirmar / Anular
    path("api/completar/<int:pk>/", views.api_completar_compra, name="api_completar_compra"),
    path("api/anular/<int:pk>/", views.api_anular_compra, name="api_anular_compra"),
]
