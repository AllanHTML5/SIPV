# inventario/urls.py
from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard-data/", views.dashboard_data, name="dashboard_data"),
    path("stock/", views.stock_list, name="stock_list"),
    path("stock/partial/", views.stock_table_partial, name="stock_table_partial"),
    path("movimientos/", views.movimientos, name="movimientos"),
    path("movimientos/partial/", views.movimientos_partial, name="movimientos_partial"),
    path("ajuste/nuevo/", views.ajuste_modal, name="ajuste_modal"),          
    path("ajuste/crear/", views.ajuste_crear, name="ajuste_crear"),       
    path("ajuste-modal/", views.ajuste_modal, name="ajuste_modal"),
    path("producto-autocomplete/", views.producto_autocomplete, name="producto_autocomplete"),

]
