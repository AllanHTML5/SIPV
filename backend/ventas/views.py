# ventas/views.py

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.timezone import now, timedelta

from django.db import transaction
from django.db.models import Q, Sum, F, Count
from django.db.models.functions import TruncDate

from decimal import Decimal
import json
from datetime import datetime, date

from maestros.models import Producto
from inventario.models import MovimientoInventario, Existencia
from common.permisos import permisos_modulos
from django.contrib.auth.models import User

from .models import Venta, VentaDetalle, Cliente
from facturas.models import Factura, FacturaDetalle
from .models import CuentaPorCobrar, Abono
from .forms import AbonoForm

def dashboard(request):
    # ============================
    # FILTROS
    # ============================
    fecha_inicio = request.GET.get("inicio")
    fecha_fin = request.GET.get("fin")
    usuario = request.GET.get("usuario")

    ventas = Venta.objects.all()
    cliente_filtro = request.GET.get("cliente")
    estado_filtro = request.GET.get("estado")

    # Filtro por fecha inicio
    if fecha_inicio:
        ventas = ventas.filter(creado__date__gte=fecha_inicio)

    # Filtro por fecha fin
    if fecha_fin:
        ventas = ventas.filter(creado__date__lte=fecha_fin)

    # Filtro por usuario/cajero
    if usuario:
        ventas = ventas.filter(creado_por__username__icontains=usuario)
    # Filtrar por cliente (nombre contiene)
    if cliente_filtro:
        ventas = ventas.filter(cliente__nombre__icontains=cliente_filtro)

    # Filtrar por estado
    if estado_filtro:
        ventas = ventas.filter(estado=estado_filtro)
    # ============================
    # TOTAL HOY
    # ============================
    hoy = timezone.localdate()
    total_dia = (
        Venta.objects.filter(creado__date=hoy)
        .aggregate(Sum("total"))["total__sum"] or 0
    )

    # ============================
    # TOTAL DEL MES
    # ============================
    hoy = timezone.localdate()
    total_mes = (
        Venta.objects.filter(creado__year=hoy.year, creado__month=hoy.month)
        .aggregate(Sum("total"))["total__sum"] or 0
    )

    # ============================
    # TOTAL DE TRANSACCIONES
    # ============================
    total_ventas = Venta.objects.count()

    # ============================
    # VENTAS RECIENTES
    # ============================
    recientes = Venta.objects.order_by("-creado")[:5]


    # === GRÁFICAS ===
    ventas_todas = Venta.objects.all()

    # --- Ventas por día ---
    ventas_por_dia = (
        ventas_todas.annotate(dia=TruncDate("creado"))
        .values("dia")
        .annotate(total_dia=Sum("total"))
        .order_by("dia")
    )

    grafica_dias = {
        "labels": [v["dia"].strftime("%d/%m") for v in ventas_por_dia],
        "data": [float(v["total_dia"]) for v in ventas_por_dia],
    }

    # --- Ventas por cajero ---
    ventas_por_cajero = (
        ventas_todas
        .values("creado_por__username")
        .annotate(total=Sum("total"))
        .order_by("creado_por__username")
    )

    grafica_cajeros = {
        "labels": [(v["creado_por__username"] or "Sin usuario") for v in ventas_por_cajero],
        "data": [float(v["total"]) for v in ventas_por_cajero],
    }





    # ============================
    # CONTEXTO FINAL
    # ============================
    contexto = {
        "ventas": ventas.order_by("-creado"),
        "recientes": recientes,

        "total_dia": total_dia,
        "total_mes": total_mes,
        "total_ventas": total_ventas,

        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,

        "grafica_dias": grafica_dias,
        "grafica_cajeros": grafica_cajeros,
    }

    return render(request, "ventas/dashboard.html", contexto)




@login_required
@permission_required("ventas.view_venta", raise_exception=True)
def pos_dashboard(request):
    """
    Pantalla principal del módulo de ventas (POS).
    Por ahora solo muestra un placeholder, luego aquí
    montamos toda la UI bonita con JS, scanner, etc.
    """
    ctx = {}
    ctx["recientes"] = Venta.objects.select_related("cajero").order_by("-creado")[:10]
    # para que la navbar sepa qué módulos mostrar
    ctx |= permisos_modulos(request.user)
    return render(request, "ventas/pos_dashboard.html", ctx)

def recientes_ventas():
    return Venta.objects.order_by("-creado")[:10]



@login_required
def api_buscar_productos(request):
    q = request.GET.get("q", "").strip()

    productos = Producto.objects.filter(
        Q(nombre__icontains=q) |
        Q(codigo_barras__icontains=q)
    ).values("id", "nombre", "precio_venta", "codigo_barras", "impuesto")[:20]

    results = [
        {
            "id": p["id"],
            "nombre": p["nombre"],
            "precio": float(p["precio_venta"]),
            "codigo": p["codigo_barras"] or "",
            "impuesto": float(p["impuesto"])
        }
        for p in productos
    ]

    return JsonResponse({"ok": True, "results": results})

@login_required
def api_buscar_clientes(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse({"results": []})

    clientes = Cliente.objects.filter(nombre__icontains=q)[:20]

    data = [
        {
            "id": c.id,
            "nombre": c.nombre,
            "telefono": c.telefono or "",
        }
        for c in clientes
    ]

    return JsonResponse({"results": data})

@login_required
def api_todos_productos(request):
    productos = Producto.objects.filter(activo=True).values(
        "id", "nombre", "precio_venta", "codigo_barras"
    )[:50]

    results = [{
        "id": p["id"],
        "nombre": p["nombre"],
        "precio": float(p["precio_venta"]),
        "codigo": p["codigo_barras"] or ""
    } for p in productos]

    return JsonResponse({"ok": True, "results": results})

@login_required
def api_agregar_linea(request):
    return JsonResponse({"ok": True})

def generar_num_venta():
    from django.db.models import Max
    ultimo = Venta.objects.aggregate(n=Max("numero"))["n"]
    if not ultimo:
        return "000001"
    return f"{int(ultimo) + 1:06d}"













@login_required
@permission_required("ventas.view_venta", raise_exception=True)
def ventas_list(request):

    q = request.GET.get("q", "").strip()
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    cajero = request.GET.get("cajero")
    metodo = request.GET.get("metodo")
    estado = request.GET.get("estado")
    ordering = request.GET.get("ordering", "-creado")

    ventas = Venta.objects.select_related("cajero", "cliente").all()

    # --- Filtros ---
    if q:
        ventas = ventas.filter(
            Q(numero__icontains=q) |
            Q(cliente__nombre__icontains=q)
        )

    if fecha_desde:
        ventas = ventas.filter(creado__date__gte=fecha_desde)

    if fecha_hasta:
        ventas = ventas.filter(creado__date__lte=fecha_hasta)

    if cajero:
        ventas = ventas.filter(cajero_id=cajero)

    if metodo:
        ventas = ventas.filter(metodo_pago=metodo)

    if estado:
        ventas = ventas.filter(estado=estado)

    ventas = ventas.order_by(ordering)

    # --- Estadísticas ---
    stats = ventas.aggregate(
        total_ventas=Sum("total"),
        total_impuestos=Sum("impuesto"),
        total_descuento=Sum("descuento_total"),
    )

    total_efectivo = ventas.filter(metodo_pago="EFECTIVO").aggregate(s=Sum("total"))["s"] or 0
    total_tarjeta = ventas.filter(metodo_pago="TARJETA").aggregate(s=Sum("total"))["s"] or 0

    # --- Paginación ---
    paginator = Paginator(ventas, 20)
    page = paginator.get_page(request.GET.get("page") or 1)

    ctx = {
        "page": page,
        "stats": stats,
        "total_efectivo": total_efectivo,
        "total_tarjeta": total_tarjeta,
        "q": q,
        "ordering": ordering,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "cajero": cajero,
        "metodo": metodo,
        "estado": estado,
    }

    ctx |= permisos_modulos(request.user)
    return render(request, "ventas/ventas_list.html", ctx)






@login_required
@permission_required("ventas.add_venta", raise_exception=True)
def crear_orden(request):
    """
    Crea una ORDEN en estado BORRADOR.
    No descuenta inventario.
    No genera totales.
    Puede ser creada por usuario o por guest (frontend).
    """
    # Generar número
    num = generar_num_venta()

    # Crear orden en borrador
    orden = Venta.objects.create(
        numero=num,
        cliente=None,
        cajero=None,             # Se asigna al pagar
        creado_por=request.user, # o None si guest
        canal="POS",
        estado="BORRADOR",
        subtotal=0,
        impuesto=0,
        total=0,
        descuento_total=0,
        metodo_pago="EFECTIVO",
        efectivo_recibido=0,
        cambio_entregado=0,
    )
    recientes = Venta.objects.order_by('-creado')[:10]

    return render(request, "ventas/pos_dashboard.html", {
        "orden": orden,
	"recientes": recientes,
    })





@login_required
@require_POST
def api_crear_orden(request):
    data = json.loads(request.body.decode("utf-8"))
    lineas = data.get("lineas", [])

    if not lineas:
        return JsonResponse({"error": "No hay productos en la orden"}, status=400)

    # crear orden BORRADOR
    orden = Venta.objects.create(
        numero=generar_num_venta(),
        cliente=None,
        cajero=None,
        creado_por=request.user,
        canal="POS",
        estado="BORRADOR",
        subtotal=0,
        impuesto=0,
        total=0,
        descuento_total=0,
        metodo_pago="EFECTIVO",
        efectivo_recibido=0,
        cambio_entregado=0,
    )

    # guardar detalles SIN descontar inventario
    for item in lineas:
        prod = Producto.objects.get(id=item["id"])
        cant = Decimal(str(item["cantidad"]))
        precio = Decimal(str(item["precio"]))

        subtotal_line = cant * precio
        impuesto_line = subtotal_line * Decimal("0.15")
        total_line = subtotal_line + impuesto_line

        VentaDetalle.objects.create(
            venta=orden,
            producto=prod,
            cantidad=cant,
            precio_unitario=precio,
            subtotal=subtotal_line,
            impuesto=impuesto_line,
            total=total_line,
        )

    return JsonResponse({
        "ok": True,
        "orden_id": orden.id,
        "orden_num": orden.numero,
    })





@require_POST
@login_required
def api_finalizar_venta(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"JSON inválido: {e}"}, status=400)

    lineas = data.get("lineas")
    pago = Decimal(data.get("pago", 0))

    if not lineas or not isinstance(lineas, list):
        return JsonResponse({"ok": False, "error": "No hay líneas en la venta."}, status=400)

    try:
        with transaction.atomic():

            # ======================================================
            # 1) GENERAR NUMERO ANTES DE CREAR LA VENTA
            # ======================================================
            ultimo = (
                Venta.objects
                .exclude(numero__isnull=True)
                .exclude(numero="")
                .order_by('-id')
                .first()
            )

            if ultimo and str(ultimo.numero).isdigit():
                nuevo_numero = str(int(ultimo.numero) + 1).zfill(6)
            else:
                nuevo_numero = "000001"

            # ======================================================
            # 2) Crear venta
            # ======================================================
            venta = Venta.objects.create(
                numero=nuevo_numero,
                creado_por=request.user,
                subtotal=0,
                impuesto=0,
                total=0
            )

            subtotal_global = Decimal("0")
            impuesto_global = Decimal("0")

            # ======================================================
            # 3) PROCESAR LÍNEAS
            # ======================================================
            for item in lineas:

                prod_id = item.get("id")
                cantidad = Decimal(item.get("cantidad", 0))

                if not prod_id or cantidad <= 0:
                    return JsonResponse({"ok": False, "error": "Formato inválido en líneas."}, status=400)

                # Obtener producto
                try:
                    prod = Producto.objects.get(id=prod_id)
                except Producto.DoesNotExist:
                    return JsonResponse({"ok": False, "error": f"Producto {prod_id} no existe."}, status=404)

                # === EXISTENCIA REAL ===
                existencia_obj, _ = Existencia.objects.get_or_create(producto=prod)
                existencia = existencia_obj.cantidad

                if cantidad > existencia:
                    return JsonResponse({
                        "ok": False,
                        "error": f"Stock insuficiente para {prod.nombre}. Disponible: {existencia}"
                    }, status=400)

                # Impuesto por producto (tu POS lo manda)
                impuesto_pct = Decimal(str(item.get("impuesto", prod.impuesto)))

                subtotal_linea = cantidad * prod.precio_venta
                impuesto_linea = subtotal_linea * impuesto_pct
                total_linea = subtotal_linea + impuesto_linea

                # Crear detalle
                VentaDetalle.objects.create(
                    venta=venta,
                    producto=prod,
                    cantidad=cantidad,
                    precio_unitario=prod.precio_venta,
                    subtotal=subtotal_linea,
                    impuesto=impuesto_linea,
                    total=total_linea,
                )

                # === RESTAR STOCK EN EXISTENCIA ===
                prod.existencia.cantidad = existencia - cantidad
                prod.existencia.save()

                # Acumular globales
                subtotal_global += subtotal_linea
                impuesto_global += impuesto_linea

            # ======================================================
            # 4) Actualizar totales
            # ======================================================
            venta.subtotal = subtotal_global
            venta.impuesto = impuesto_global
            venta.total = subtotal_global + impuesto_global
            venta.save()

            return JsonResponse({
                "ok": True,
                "venta_id": venta.id,
                "venta_num": venta.numero,
                "total": float(venta.total)
            })

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)



@require_POST
@login_required
def api_pago(request):
    """
    Finaliza la orden, registra pago y sustrae stock.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    venta_id = data.get("venta_id")
    metodo = data.get("metodo")
    ref = data.get("ref", "")
    pago = Decimal(data.get("pago", 0))
    lineas = data.get("lineas", [])

    if not venta_id:
        return JsonResponse({"ok": False, "error": "Falta venta_id"}, status=400)

    if metodo not in ["EFECTIVO", "TARJETA", "TRANSFERENCIA", "CREDITO"]:
        return JsonResponse({"ok": False, "error": "Método no válido"}, status=400)

    # Obtener la venta
    try:
        venta = Venta.objects.get(id=venta_id)
    except Venta.DoesNotExist:
        return JsonResponse({"ok": False, "error": "La orden no existe"}, status=404)

    if venta.estado == "COMPLETADA":
        return JsonResponse({"ok": False, "error": "Esta orden ya fue completada"}, status=400)

    try:
        with transaction.atomic():

            # -------------------------------------------------------------------
            # 1) RECONSTRUIR TOTALES SEGÚN CANTIDADES EDITADAS
            # -------------------------------------------------------------------
            venta.detalles.all().delete()

            subtotal_global = Decimal(0)
            impuesto_global = Decimal(0)

            for l in lineas:
                prod_id = l.get("id")
                cantidad = Decimal(l.get("cantidad", 0))
                impuesto_pct = Decimal(str(l.get("impuesto")))

                if not prod_id or cantidad <= 0:
                    return JsonResponse({"ok": False, "error": "Línea inválida"}, status=400)

                try:
                    prod = Producto.objects.get(id=prod_id)
                except:
                    return JsonResponse({"ok": False, "error": "Producto inválido"}, status=404)

                precio = prod.precio_venta
                subtotal = precio * cantidad
                impuesto = subtotal * impuesto_pct
                total = subtotal + impuesto

                # Crear detalle actualizado
                VentaDetalle.objects.create(
                    venta=venta,
                    producto=prod,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal,
                    impuesto=impuesto,
                    total=total
                )

                subtotal_global += subtotal
                impuesto_global += impuesto

            venta.subtotal = subtotal_global
            venta.impuesto = impuesto_global
            venta.total = subtotal_global + impuesto_global

            # -------------------------------------------------------------------
            # 2) VALIDAR PAGO SEGÚN MÉTODO
            # -------------------------------------------------------------------

            if metodo == "EFECTIVO":
                if pago < venta.total:
                    return JsonResponse({"ok": False, "error": "Pago insuficiente"}, status=400)

            if metodo in ["TARJETA", "TRANSFERENCIA"] and len(ref.strip()) == 0:
                return JsonResponse({"ok": False, "error": "Debe ingresar referencia"}, status=400)

            # CRÉDITO NO REQUIERE VALIDACIÓN

            # -------------------------------------------------------------------
            # 3) REGISTRAR PAGO EN LA VENTA
            # -------------------------------------------------------------------
            venta.metodo_pago = metodo
            venta.pago = pago
            venta.referencia = ref
            venta.estado = "COMPLETADA"
            venta.save()

            # -------------------------------------------------------------------
            # 4) SUSTRAER STOCK SOLO AL COMPLETAR LA ORDEN
            # -------------------------------------------------------------------
            for det in venta.detalles.all():

                existencia, _ = Existencia.objects.get_or_create(
                    producto=det.producto
                )

                if existencia.cantidad < det.cantidad:
                    raise ValueError(f"Stock insuficiente para {det.producto.nombre}")

                existencia.cantidad -= det.cantidad
                existencia.save()

                # Registrar movimiento
                MovimientoInventario.objects.create(
                    producto=det.producto,
                    tipo="SALIDA",
                    cantidad=det.cantidad,
                    costo_unitario=det.precio_unitario,
                    referencia=f"VENTA-{venta.id}",
                    motivo="Salida por venta",
                    usuario=request.user
                )

            return JsonResponse({
                "ok": True,
                "venta_id": venta.id,
                "venta_num": venta.numero,
                "total": float(venta.total)
            })

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def detalle(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.select_related("producto")
    factura = Factura.objects.filter(numero=f"FV-{venta.numero}").first()

    return render(request, "ventas/detalle.html", {
        "venta": venta,
        "detalles": detalles,
        "clientes": Cliente.objects.all().order_by("nombre"),
        "factura": factura,
    })



@transaction.atomic
def api_completar_venta(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    venta = get_object_or_404(Venta, pk=pk)

    data = json.loads(request.body.decode("utf-8"))
    metodo = data.get("metodo")
    efectivo = data.get("efectivo", 0)
    referencia = data.get("referencia", "")
    cliente_id = data.get("cliente")

    # -----------------------------
    # VALIDACIONES
    # -----------------------------
    if metodo == "EFECTIVO" and float(efectivo) < float(venta.total):
        return JsonResponse({"ok": False, "error": "El efectivo recibido es insuficiente."}, status=400)

    if metodo in ("TARJETA", "TRANSFERENCIA") and not referencia:
        return JsonResponse({"ok": False, "error": "Debe ingresar referencia del pago."}, status=400)

    if metodo == "CREDITO" and not cliente_id:
        return JsonResponse({"ok": False, "error": "Debe seleccionar cliente para crédito."}, status=400)

    # -----------------------------
    # GUARDAR DATOS DE PAGO
    # -----------------------------
    venta.metodo_pago = metodo
    venta.efectivo_recibido = efectivo
    venta.cambio_entregado = max(0, float(efectivo) - float(venta.total))
    venta.referencia_pago = referencia
    venta.cajero = request.user
    if cliente_id:
        venta.cliente_id = cliente_id

    venta.estado = "PAGADA"
    venta.cajero = request.user
    venta.save()

    # -----------------------------
    # DESCONTAR STOCK + MOVIMIENTO
    # -----------------------------
    for d in venta.detalles.all():
        ex = d.producto.existencia
        ex.cantidad -= d.cantidad
        ex.save()

        MovimientoInventario.objects.create(
            producto=d.producto,
            tipo="SALIDA",
            cantidad=d.cantidad,
            costo_unitario=d.precio_unitario,
            referencia=f"VENTA-{venta.numero}",
            motivo="Venta POS",
            usuario=venta.creado_por
        )

    # ============================================================
    #   🔥 GENERAR FACTURA AUTOMÁTICAMENTE (INTEGRACIÓN COMPLETA)
    # ============================================================


    factura = Factura.objects.create(
        tipo="VENTA",
        numero=f"FV-{venta.numero}",
        cliente=venta.cliente,
        fecha=timezone.now(),
        subtotal=venta.subtotal,
        impuesto=venta.impuesto,
        total=venta.total,
        metodo_pago=venta.metodo_pago,
        referencia_pago=venta.referencia_pago,
        efectivo_recibido=venta.efectivo_recibido,
        cambio_entregado=venta.cambio_entregado,
        creado_por=request.user,
        venta=venta,
    )

    # Crear líneas de factura
    for det in venta.detalles.all():
        FacturaDetalle.objects.create(
            factura=factura,
            producto=det.producto,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            subtotal=det.subtotal,
            impuesto=det.impuesto,
            total=det.total
        )

    # ============================================================

    return JsonResponse({"ok": True, "venta": venta.numero, "factura_id": factura.id})


    
# ============================
# AGREGAR PRODUCTO A LA ORDEN
# ============================
@require_POST
@login_required
def api_linea_agregar(request):
    data = json.loads(request.body.decode("utf-8"))
    venta_id = data.get("venta_id")
    prod_id = data.get("producto_id")
    cantidad = Decimal(str(data.get("cantidad", 1)))

    if not venta_id or not prod_id:
        return JsonResponse({"ok": False, "error": "Datos incompletos"}, status=400)

    venta = get_object_or_404(Venta, pk=venta_id)
    prod = get_object_or_404(Producto, pk=prod_id)

    # Crear o sumar
    linea, created = VentaDetalle.objects.get_or_create(
        venta=venta,
        producto=prod,
        defaults={
            "cantidad": cantidad,
            "precio_unitario": prod.precio_venta,
            "subtotal": cantidad * prod.precio_venta,
            "impuesto": (cantidad * prod.precio_venta) * prod.impuesto,
            "total": (cantidad * prod.precio_venta) * (1 + prod.impuesto),
        }
    )

    # Si ya existía → sumar
    if not created:
        linea.cantidad += cantidad
        linea.subtotal = linea.cantidad * prod.precio_venta
        linea.impuesto = linea.subtotal * prod.impuesto
        linea.total = linea.subtotal + linea.impuesto
        linea.save()

    # actualizar totales de la venta
    totales = venta.detalles.aggregate(
        subtotal=Sum("subtotal"),
        impuesto=Sum("impuesto"),
        total=Sum("total"),
    )

    venta.subtotal = totales["subtotal"] or 0
    venta.impuesto = totales["impuesto"] or 0
    venta.total = totales["total"] or 0
    venta.save()

    return JsonResponse({
        "ok": True,
        "linea": {
            "id": linea.id,
            "producto": prod.nombre,
            "cantidad": float(linea.cantidad),
            "precio": float(prod.precio_venta),
            "subtotal": float(linea.total),
        },
        "totales": {
            "subtotal": float(venta.subtotal),
            "impuesto": float(venta.impuesto),
            "total": float(venta.total),
        }
    })


# ============================
# ACTUALIZAR CANTIDAD
# ============================
@require_POST
@login_required
def api_linea_actualizar(request):
    data = json.loads(request.body.decode("utf-8"))
    linea_id = data.get("linea_id")
    cantidad = Decimal(str(data.get("cantidad", 1)))

    linea = get_object_or_404(VentaDetalle, pk=linea_id)
    venta = linea.venta

    # actualizar cantidad
    linea.cantidad = cantidad
    linea.subtotal = cantidad * linea.precio_unitario
    linea.impuesto = linea.subtotal * linea.producto.impuesto
    linea.total = linea.subtotal + linea.impuesto
    linea.save()

    # actualizar totales globales
    totales = venta.detalles.aggregate(
        subtotal=Sum("subtotal"),
        impuesto=Sum("impuesto"),
        total=Sum("total")
    )

    venta.subtotal = totales["subtotal"] or 0
    venta.impuesto = totales["impuesto"] or 0
    venta.total = totales["total"] or 0
    venta.save()

    return JsonResponse({
        "ok": True,
        "linea_total": float(linea.total),
        "totales": {
            "subtotal": float(venta.subtotal),
            "impuesto": float(venta.impuesto),
            "total": float(venta.total),
        }
    })


# ============================
# ELIMINAR LÍNEA
# ============================
@require_POST
@login_required
def api_linea_eliminar(request):
    data = json.loads(request.body.decode("utf-8"))
    linea_id = data.get("linea_id")

    linea = get_object_or_404(VentaDetalle, pk=linea_id)
    venta = linea.venta
    linea.delete()

    # recalcular totales de la venta
    totales = venta.detalles.aggregate(
        subtotal=Sum("subtotal"),
        impuesto=Sum("impuesto"),
        total=Sum("total")
    )

    venta.subtotal = totales["subtotal"] or 0
    venta.impuesto = totales["impuesto"] or 0
    venta.total = totales["total"] or 0
    venta.save()

    return JsonResponse({
        "ok": True,
        "totales": {
            "subtotal": float(venta.subtotal),
            "impuesto": float(venta.impuesto),
            "total": float(venta.total),
        }
    })

def ventas_recientes_api(request):
    data = [
        {
            "id": v.id,
            "numero": v.numero,
            "fecha": v.creado.strftime("%Y-%m-%d %H:%M"),
            "total": float(v.total),
            "usuario": v.creado_por.get_full_name() if v.creado_por else "Sistema"
        }
        for v in Venta.objects.order_by("-creado")[:20]
    ]
    return JsonResponse({"recientes": data})

@login_required
def api_lineas(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)

    detalles = venta.detalles.select_related("producto__categoria", "producto__proveedor")

    lineas = []
    for d in detalles:

        p = d.producto

        # Stock real
        stock = 0
        if hasattr(p, "existencia") and p.existencia:
            stock = float(p.existencia.cantidad)

        lineas.append({
            "id": d.id,
            "producto_id": p.id,
            "nombre": p.nombre,
            "codigo": p.codigo_barras or "",
            "categoria": p.categoria.nombre if p.categoria else "",
            "proveedor": p.proveedor.nombre if p.proveedor else "",
            "impuesto": float(p.impuesto),  # porcentaje real (0.15)
            "stock": stock,

            # Datos de la línea
            "cantidad": float(d.cantidad),
            "precio": float(d.precio_unitario),
            "subtotal": float(d.subtotal),
            "impuesto_valor": float(d.impuesto),
            "total": float(d.total),
        })

    totales = {
        "subtotal": float(venta.subtotal),
        "impuesto": float(venta.impuesto),
        "total": float(venta.total),
    }

    return JsonResponse({"ok": True, "lineas": lineas, "totales": totales})

def api_producto_info(request, pk):
    p = Producto.objects.get(pk=pk)

    return JsonResponse({
        "id": p.id,
        "nombre": p.nombre,
        "codigo": p.codigo_barras or "",
        "categoria": p.categoria.nombre if p.categoria else "",
        "proveedor": p.proveedor.nombre if p.proveedor else "",
        "precio": float(p.precio_venta),
        "impuesto": float(p.impuesto),
        "stock": float(p.existencia.cantidad) if hasattr(p, "existencia") else 0,
    })

# ============================
#  CANCELAR ORDEN (BORRADOR)
# ============================
@require_POST
@login_required
def api_cancelar_orden(request, pk):
    venta = get_object_or_404(Venta, pk=pk)

    if venta.estado != "BORRADOR":
        return JsonResponse({
            "ok": False,
            "error": "Solo se pueden cancelar órdenes en borrador."
        }, status=400)

    # Borrar las líneas
    venta.detalles.all().delete()

    # Marcar como cancelada
    venta.estado = "CANCELADA"
    venta.total = 0
    venta.subtotal = 0
    venta.impuesto = 0
    venta.save()

    return JsonResponse({"ok": True})
# ============================
#   ANULAR ORDEN YA PAGADA
# ============================
@require_POST
@login_required
def api_anular_orden(request, pk):
    venta = get_object_or_404(Venta, pk=pk)

    if venta.estado != "PAGADA":
        return JsonResponse({
            "ok": False,
            "error": "Solo se pueden anular órdenes pagadas."
        }, status=400)

    # Revertir stock por cada línea
    for d in venta.detalles.select_related("producto").all():
        prod = d.producto

        # Revertir existencia solo si el inventario está enlazado
        if hasattr(prod, "existencia"):
            prod.existencia.cantidad += d.cantidad
            prod.existencia.save()

    # Cambiar estado
    venta.estado = "ANULADA"
    venta.save()

    return JsonResponse({"ok": True})

def api_cliente_info(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Cliente no encontrado"}, status=404)

    # Total de compras del cliente (solo PAGADAS)
    total = (
        Venta.objects.filter(cliente=cliente, estado="PAGADA")
        .aggregate(total=Sum("total"))
        .get("total") or 0
    )

    return JsonResponse({
        "ok": True,
        "id": cliente.id,
        "nombre": cliente.nombre,
        "telefono": cliente.telefono or "",
        "email": cliente.email or "",
        "total_compras": float(total),
    })
@login_required
def cartera_dashboard(request):
    hoy = timezone.now().date()

    vigente = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0,
        fecha_vencimiento__gte=hoy
    )

    vencida = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0,
        fecha_vencimiento__lt=hoy
    )

    vigente_total = vigente.aggregate(total=Sum("saldo_pendiente"))["total"] or 0
    vencida_total = vencida.aggregate(total=Sum("saldo_pendiente"))["total"] or 0
    total = vigente_total + vencida_total

    clientes_con_deuda = (
        CuentaPorCobrar.objects
        .filter(saldo_pendiente__gt=0)
        .values("cliente")
        .distinct()
        .count()
    )

    # -----------------------------------------------------
    # CRÉDITO DIARIO (últimos 7 días para el gráfico)
    # -----------------------------------------------------
    dias_labels = []
    dias_valores = []

    for i in range(7):
        dia = hoy - timedelta(days=i)
        valor = (
            CuentaPorCobrar.objects
            .filter(creado__date=dia)
            .aggregate(total=Sum("monto_total"))["total"]
            or 0
        )
        dias_labels.append(dia.strftime("%d/%m"))
        dias_valores.append(float(valor))

    dias_labels.reverse()
    dias_valores.reverse()

    # -----------------------------------------------------
    # CRÉDITOS RECIENTES (últimos 10)
    # -----------------------------------------------------
    recientes = (
        CuentaPorCobrar.objects
        .select_related("cliente", "venta")
        .order_by("-creado")[:10]
    )

    context = {
        "vigente_total": vigente_total,
        "vencida_total": vencida_total,
        "total": total,
        "clientes_con_deuda": clientes_con_deuda,
        "credito_diario": sum(dias_valores),
        "dias_labels": dias_labels,
        "dias_valores": dias_valores,
        "recientes": recientes,
    }

    return render(request, "ventas/cartera_dashboard.html", context)



@login_required
def cartera_pendientes(request):
    hoy = timezone.now().date()
    cuentas = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0, fecha_vencimiento__gte=hoy
    )
    return render(request, "ventas/cartera_pendientes.html", {"cuentas": cuentas})

@login_required
def cartera_vencidas(request):
    hoy = timezone.now().date()
    cuentas = CuentaPorCobrar.objects.filter(
        saldo_pendiente__gt=0, fecha_vencimiento__lt=hoy
    )
    return render(request, "ventas/cartera_vencidas.html", {"cuentas": cuentas})

@login_required
def cartera_detalle(request, pk):
    cuenta = get_object_or_404(CuentaPorCobrar, pk=pk)
    abonos = cuenta.abonos.all()

    # ================================
    # Buscar factura SIN usar venta_id
    # ================================
    factura = None
    if cuenta.venta and cuenta.venta.numero:
        factura = Factura.objects.filter(
            numero=f"FV-{cuenta.venta.numero}"
        ).first()

    return render(request, "ventas/cartera_detalle.html", {
        "cuenta": cuenta,
        "abonos": abonos,
        "factura": factura,
    })

@login_required
def abonos_list(request, pk):
    cuenta = get_object_or_404(CuentaPorCobrar, pk=pk)
    abonos = cuenta.abonos.all()

    return render(request, "ventas/abonos_list.html", {
        "cuenta": cuenta,
        "abonos": abonos,
    })

@login_required
def abono_create(request, pk):
    cuenta = get_object_or_404(CuentaPorCobrar, pk=pk)

    if request.method == "POST":
        form = AbonoForm(request.POST)

        if form.is_valid():
            abono = form.save(commit=False)

            # Asignamos la cuenta ANTES de validar montos
            abono.cuenta = cuenta

            # Validación manual contra el saldo
            if abono.monto <= 0:
                form.add_error("monto", "El abono debe ser mayor a 0.")
            elif abono.monto > cuenta.saldo_pendiente:
                form.add_error("monto", "El abono no puede ser mayor al saldo pendiente.")

            if not form.errors:
                abono.save()
                return redirect("ventas:cartera_detalle", pk=pk)

    else:
        form = AbonoForm()

    return render(request, "ventas/abono_form.html", {
        "cuenta": cuenta,
        "form": form
    })


@login_required
def detalle_credito_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    # Todas las cuentas del cliente
    cuentas = CuentaPorCobrar.objects.filter(cliente=cliente)

    # Totales
    total_credito = cuentas.aggregate(t=Sum("monto_total"))["t"] or 0
    saldo_pendiente = cuentas.aggregate(s=Sum("saldo_pendiente"))["s"] or 0
    total_abonado = total_credito - saldo_pendiente

    # Créditos recientes (últimos 10)
    creditos_recientes = cuentas.order_by("-creado")[:10]

    # Abonos recientes (últimos 15)
    abonos_recientes = (
        Abono.objects.filter(cuenta__cliente=cliente)
        .select_related("cuenta")
        .order_by("-fecha")[:15]
    )

    return render(request, "ventas/detalle_credito_cliente.html", {
        "cliente": cliente,
        "total_credito": total_credito,
        "total_abonado": total_abonado,
        "saldo_pendiente": saldo_pendiente,
        "creditos_recientes": creditos_recientes,
        "abonos_recientes": abonos_recientes,
    })
