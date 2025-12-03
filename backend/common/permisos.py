# common/permisos.py


def permisos_modulos(request):
    user = request.user
    """
    Devuelve flags de qué módulos puede ver el usuario,
    para usarlos en la navbar (base.html) y en los dashboards.
    """
    if not user.is_authenticated:
        return {
            "puede_inventario": False,
            "puede_compras": False,
            "puede_maestros": False,
            "puede_ventas": False,
	    "puede_facturas": False,

        }

    puede_inventario = (
        user.has_perm("inventario.view_movimientoinventario")
        or user.has_perm("inventario.view_existencia")
        or user.has_perm("maestros.view_producto")
    )

    puede_compras = user.has_perm("compras.view_compra")

    puede_maestros = (
        user.has_perm("maestros.view_producto")
        or user.has_perm("maestros.view_proveedor")
        or user.has_perm("maestros.view_categoria")
    )

    puede_ventas = user.has_perm("ventas.view_venta")
    puede_facturas = user.has_perm("facturas.view_factura")
    return {
        "puede_inventario": puede_inventario,
        "puede_compras": puede_compras,
        "puede_maestros": puede_maestros,
        "puede_ventas": puede_ventas,
        "puede_facturas": puede_facturas,
    }
