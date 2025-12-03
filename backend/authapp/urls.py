from django.urls import path
from . import views

app_name = "authapp"

urlpatterns = [
    # Dashboard principal
    path("", views.auth_dashboard, name="dashboard"),

    # Usuarios
    path("usuarios/", views.usuarios_lista, name="usuarios_lista"),
    path("usuarios/nuevo/", views.usuarios_crear, name="usuarios_crear"),
    path("usuarios/<int:pk>/editar/", views.usuarios_editar, name="usuarios_editar"),
    path("usuarios/<int:pk>/eliminar/", views.usuarios_eliminar, name="usuarios_eliminar"),
    path("usuarios/<int:pk>/password/", views.usuarios_cambiar_password, name="usuarios_password"),
    path("usuarios/buscar/", views.usuarios_buscar, name="usuarios_buscar"),
   
    # Grupos
    path("grupos/", views.grupos_lista, name="grupos_lista"),
    path("grupos/nuevo/", views.grupos_crear, name="grupos_crear"),
    path("grupos/<int:pk>/editar/", views.grupos_editar, name="grupos_editar"),
    path("grupos/<int:pk>/eliminar/", views.grupos_eliminar, name="grupos_eliminar"),
    path("grupos/buscar/", views.grupos_buscar, name="grupos_buscar"),

    # PERMISOS (solo lectura)
    path("permisos/", views.permisos_lista, name="permisos_lista"),
    path("permisos/buscar/", views.permisos_buscar, name="permisos_buscar"),
    path("permisos/<int:pk>/", views.permisos_detalle, name="permisos_detalle"),



]
