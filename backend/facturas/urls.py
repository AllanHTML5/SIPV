from django.urls import path
from . import views

app_name = "facturas"

urlpatterns = [
    path("dashboard/", views.facturas_list, name="dashboard"),

    path("", views.facturas_list, name="list"),
    path("<int:pk>/", views.factura_detalle, name="detalle"),


    # API REST
    path("api/list/", views.api_facturas_list, name="api_list"),
    path("<int:pk>/pdf/", views.factura_pdf, name="factura_pdf"),
    path("api/crear/", views.api_factura_crear, name="api_crear"),
    path("venta/<int:pk>/pdf/", views.factura_venta_pdf, name="venta_pdf"),
    path("compra/<int:pk>/pdf/", views.factura_compra_pdf, name="compra_pdf"),
    path("<int:pk>/ticket/", views.factura_ticket, name="factura_ticket"),


]
