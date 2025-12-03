from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from . import views

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from maestros.api import CategoriaViewSet, ProveedorViewSet, ProductoViewSet
router = routers.DefaultRouter()
router.register(r'categorias', CategoriaViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'productos', ProductoViewSet)

urlpatterns = [
    path("", views.home_dashboard, name="home"),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("inventario/", include("inventario.urls", namespace="inventario")),
    path("compras/", include("compras.urls", namespace="compras")),
    path("ventas/", include("ventas.urls", namespace="ventas")),
    path("facturas/", include("facturas.urls", namespace="facturas")),
    path("maestros/", include("maestros.urls", namespace="maestros")),
    path("auth/", include("authapp.urls", namespace="authapp")),
]

# MEDIA (imagenes)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# STATICFILES (CSS, JS, admin, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
