from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "maestros"

urlpatterns = [
    path("", lambda request: redirect("maestros:dashboard"), name="root"),
    # -----------------------------------------------------
    # CATEGORÍAS
    # -----------------------------------------------------
    path("categorias/", views.categorias_lista, name="categorias_lista"),
    path("categorias/nueva/", views.categorias_crear, name="categorias_crear"),
    path("categorias/<int:pk>/editar/", views.categorias_editar, name="categorias_editar"),
    path("categorias/<int:pk>/eliminar/", views.categorias_eliminar, name="categorias_eliminar"),

    # -----------------------------------------------------
    # PRODUCTOS
    # -----------------------------------------------------
    path("productos/", views.productos_lista, name="productos_lista"),
    path("productos/nuevo/", views.productos_crear, name="productos_crear"),
    path("productos/<int:pk>/editar/", views.productos_editar, name="productos_editar"),
    path("productos/<int:pk>/eliminar/", views.productos_eliminar, name="productos_eliminar"),

    # Detalle individual (opcional pero pro)
    path("productos/<int:pk>/", views.productos_detalle, name="productos_detalle"),

    # Buscador AJAX (si lo usas)
    path("productos/buscar/", views.productos_buscar, name="productos_buscar"),

    # -----------------------------------------------------
    # PROVEEDORES
    # -----------------------------------------------------
    path("proveedores/", views.proveedores_lista, name="proveedores_lista"),
    path("proveedores/nuevo/", views.proveedores_crear, name="proveedores_crear"),
    path("proveedores/<int:pk>/editar/", views.proveedores_editar, name="proveedores_editar"),
    path("proveedores/<int:pk>/eliminar/", views.proveedores_eliminar, name="proveedores_eliminar"),

    # CLIENTES
    path("clientes/", views.clientes_lista, name="clientes_lista"),
    path("clientes/nuevo/", views.clientes_crear, name="clientes_crear"),
    path("clientes/<int:pk>/editar/", views.clientes_editar, name="clientes_editar"),
    path("clientes/<int:pk>/eliminar/", views.clientes_eliminar, name="clientes_eliminar"),
    path("clientes/<int:pk>/", views.clientes_detalle, name="clientes_detalle"),


    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------
    path("dashboard/", views.maestros_dashboard, name="dashboard"),

]
