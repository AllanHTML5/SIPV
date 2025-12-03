import json
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce, TruncDate
from django.db.models import DecimalField
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q

from .models import Compra, CompraDetalle
from maestros.models import Proveedor, Producto
from .forms import CompraForm, CompraDetalleFormSet
from common.permisos import permisos_modulos
from facturas.models import Factura, FacturaDetalle
from inventario.models import MovimientoInventario

@login_required
@permission_required("compras.add_compra", raise_exception=True)
def crear_compra_borrador(request):
    """
    Crea una compra BORRADOR y redirige al POS de compras.
    """
    compra = Compra.objects.create(
        proveedor=None,
        fecha=timezone.now(),
        creado_por=request.user,
        estado="BORRADOR",
        subtotal=0,
        impuesto=0,
        total=0,
        tasa_impuesto=Decimal("15.00"),
    )

    return redirect("compras:detalle", pk=compra.pk)
@login_required
def detalle_pos_compra(request, pk):
    compra = get_object_or_404(
        Compra.objects.select_related("proveedor").prefetch_related("detalles__producto"),
        pk=pk
    )

    proveedores = Proveedor.objects.filter(estado=True)
    factura = Factura.objects.filter(numero=f"FC-{compra.id}").first()

    return render(request, "compras/pos_detalle.html", {
        "compra": compra,
        "proveedores": proveedores,
        "factura": factura,
    })

# ---------- Dashboard & charts ----------
@login_required
def dashboard(request):
    hoy = timezone.localdate()
    inicio_30 = hoy - timezone.timedelta(days=30)

    # KPIs
    compras_30_qs = Compra.objects.filter(
        fecha__gte=inicio_30,
        estado="CONFIRMADA"
    )

    dec2 = DecimalField(max_digits=14, decimal_places=2)

    kpis = {
        # Proveedores activos
        "proveedores_activos": Proveedor.objects.filter(estado=True).count(),

        # Compras confirmadas últimos 30 días
        "compras_30d": compras_30_qs.count(),

        # Monto total últimos 30 días
        "monto_30d": compras_30_qs.aggregate(
            x=Coalesce(Sum("total", output_field=dec2), Value(0, output_field=dec2))
        )["x"],

        # Últimas confirmadas (mantengo esta por compatibilidad)
        "ult_conf": Compra.objects.filter(estado="CONFIRMADA")
            .select_related("proveedor")
            .order_by("-fecha", "-id")[:5],
    }

    ult_compras = (
        Compra.objects.select_related("proveedor")
        .order_by("-fecha", "-id")[:10]
    )
    kpis["ult_compras"] = ult_compras

    # Variaciones 30 días

    inicio_60 = inicio_30 - timezone.timedelta(days=30)
    compras_prev_qs = Compra.objects.filter(
        fecha__gte=inicio_60,
        fecha__lt=inicio_30,
        estado="CONFIRMADA"
    )

    monto_prev = compras_prev_qs.aggregate(
        total=Coalesce(Sum("total", output_field=dec2), Value(0, output_field=dec2))
    )["total"]

    monto_actual = kpis["monto_30d"]

    if monto_prev and monto_prev > 0:
        variacion_monto = ((monto_actual - monto_prev) / monto_prev) * 100
    else:
        variacion_monto = 0

    compras_prev_count = compras_prev_qs.count()
    compras_actual_count = kpis["compras_30d"]

    if compras_prev_count and compras_prev_count > 0:
        variacion_volumen = (
            (compras_actual_count - compras_prev_count) / compras_prev_count
        ) * 100
    else:
        variacion_volumen = 0

    kpis["variacion_monto_30d"] = variacion_monto
    kpis["variacion_volumen_30d"] = variacion_volumen


    # SERIES PARA GRÁFICOS

    comp = (
        compras_30_qs.annotate(d=TruncDate("fecha"))
        .values("d")
        .annotate(
            total=Coalesce(Sum("total", output_field=dec2), Value(0, output_field=dec2))
        )
        .order_by("d")
    )

    labels_30 = [c["d"].strftime("%Y-%m-%d") for c in comp]
    vals_30 = [float(c["total"]) for c in comp]

    # Top productos por cantidad
    dec3 = DecimalField(max_digits=14, decimal_places=3)
    top_qs = (
        CompraDetalle.objects.filter(
            compra__estado="CONFIRMADA",
            compra__fecha__gte=inicio_30
        )
        .values("producto__nombre")
        .annotate(
            q=Coalesce(Sum("cantidad", output_field=dec3), Value(0, output_field=dec3))
        )
        .order_by("-q")[:10]
    )

    top_labels = [t["producto__nombre"] for t in top_qs]
    top_vals = [float(t["q"]) for t in top_qs]

    # Monto por proveedor
    prov_qs = (
        compras_30_qs.values("proveedor__nombre")
        .annotate(
            monto=Coalesce(Sum("total", output_field=dec2), Value(0, output_field=dec2))
        )
        .order_by("-monto")[:10]
    )

    prov_labels = [p["proveedor__nombre"] for p in prov_qs]
    prov_vals = [float(p["monto"]) for p in prov_qs]

    # Datos para JS
    chart_data = {
        "compras_30d": {"labels": labels_30, "values": vals_30},
        "top_productos": {"labels": top_labels, "values": top_vals},
        "por_proveedor": {"labels": prov_labels, "values": prov_vals},
    }


    # CONTEXTO FINAL



    ctx = {
        **kpis,
        "ult_compras": ult_compras,
        "chart_data_json": json.dumps(chart_data, cls=DjangoJSONEncoder),
    }

    return render(request, "compras/dashboard.html", ctx)

@login_required
def dashboard_data(request):
    hoy = timezone.localdate()
    inicio_30 = hoy - timezone.timedelta(days=30)


    dec2 = DecimalField(max_digits=14, decimal_places=2)
    comp = (
        Compra.objects.filter(fecha__gte=inicio_30, estado="CONFIRMADA")
        .annotate(d=TruncDate("fecha"))
        .values("d")
        .annotate(total=Coalesce(Sum("total", output_field=dec2), 0))
        .order_by("d")
    )
    labels = [c["d"].strftime("%Y-%m-%d") for c in comp]
    valores = [float(c["total"]) for c in comp]


    dec3 = DecimalField(max_digits=14, decimal_places=3)
    top_qs = (
        CompraDetalle.objects.filter(
            compra__estado="CONFIRMADA", compra__fecha__gte=inicio_30
        )
        .values("producto__nombre")
        .annotate(q=Coalesce(Sum("cantidad", output_field=dec3), 0))
        .order_by("-q")[:10]
    )
    top_labels = [t["producto__nombre"] for t in top_qs]
    top_vals = [float(t["q"]) for t in top_qs]


    prov_qs = (
        Compra.objects.filter(estado="CONFIRMADA", fecha__gte=inicio_30)
        .values("proveedor__nombre")
        .annotate(monto=Coalesce(Sum("total", output_field=dec2), 0))
        .order_by("-monto")[:10]
    )
    prov_labels = [p["proveedor__nombre"] for p in prov_qs]
    prov_vals = [float(p["monto"]) for p in prov_qs]

    data = {
        "compras_30d": {"labels": labels, "values": valores},
        "top_productos": {"labels": top_labels, "values": top_vals},
        "por_proveedor": {"labels": prov_labels, "values": prov_vals},
        "is_empty": (
            len(labels) == 0 and len(top_labels) == 0 and len(prov_labels) == 0
        ),
    }
    return JsonResponse(data)




@login_required
def lista(request):
    qs = Compra.objects.select_related("proveedor").order_by("-fecha", "-id")

    # filtros
    estado = request.GET.get("estado")
    proveedor = request.GET.get("proveedor")
    fecha_desde = request.GET.get("desde")
    fecha_hasta = request.GET.get("hasta")
    total_min = request.GET.get("total_min")
    total_max = request.GET.get("total_max")

    if estado:
        qs = qs.filter(estado=estado)

    if proveedor:
        qs = qs.filter(proveedor_id=proveedor)

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    if total_min:
        qs = qs.filter(total__gte=total_min)

    if total_max:
        qs = qs.filter(total__lte=total_max)

    return render(request, "compras/lista.html", {
        "compras": qs,
        "estado": estado,
        "proveedor": proveedor,
        "desde": fecha_desde,
        "hasta": fecha_hasta,
        "total_min": total_min,
        "total_max": total_max,
        "proveedores": Proveedor.objects.all()
    })


@login_required
@permission_required("compras.add_compra", raise_exception=True)
def crear(request):
    if request.method == "POST":
        form = CompraForm(request.POST)
        formset = CompraDetalleFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Crear compra pero sin guardar totales todavía
            compra = form.save(commit=False)
            # Impuesto fijo 15% (en el modelo está como 15.00)
            compra.tasa_impuesto = Decimal("15.00")
            compra.save()

            # Vincular detalles a la compra
            formset.instance = compra
            formset.save()

            # Calcular totales desde los detalles
            subtotal, impuesto, total = compra.calcular_totales()
            compra.subtotal = subtotal
            compra.impuesto = impuesto
            compra.total = total
            compra.save(update_fields=["subtotal", "impuesto", "total"])

            messages.success(request, "Compra creada exitosamente.")
            return redirect("compras:detalle", pk=compra.pk)
        else:
            messages.error(
                request,
                "No se pudo crear la compra. Revisa los errores en el formulario.",
            )
    else:
        form = CompraForm()
        formset = CompraDetalleFormSet()

    return render(
        request,
        "compras/crear.html",
        {
            "form": form,
            "formset": formset,
            "proveedores": Proveedor.objects.filter(estado=True)
        },
    )



@login_required
def detalle(request, pk):
    compra = get_object_or_404(
        Compra.objects.select_related("proveedor").prefetch_related("detalles__producto"),
        pk=pk
    )

    detalles = []
    factura = Factura.objects.filter(numero=f"FC-{compra.pk}").first()

    for d in compra.detalles.all():
        subtotal = d.cantidad * d.costo_unitario
        impuesto = subtotal * Decimal("0.15")
        detalles.append({
            "obj": d,
            "subtotal": subtotal,
            "impuesto": impuesto
        })

    return render(request, "compras/detalle.html", {
        "compra": compra,
        "detalles": detalles,
        "factura": factura,
    })



@login_required
@permission_required("compras.change_compra", raise_exception=True)
def confirmar(request, pk):
    compra = get_object_or_404(Compra.objects.prefetch_related("detalles"), pk=pk)


    # Estado

    if compra.estado != "CONFIRMADA":
        compra.estado = "CONFIRMADA"
        compra.save(update_fields=["estado"])
    # Materializar movimientos (entradas de inventario)

    compra.materializar_movimientos()


    # Verificar si ya existe factura (idempotente)
    factura = Factura.objects.filter(tipo="COMPRA", numero=f"FC-{compra.id}").first()

    if not factura:
        factura = Factura.objects.create(
            tipo="COMPRA",
            numero=f"FC-{compra.id}",
            proveedor=compra.proveedor,
            fecha=timezone.now(),
            subtotal=compra.subtotal,
            impuesto=compra.impuesto,
            total=compra.total,
            metodo_pago=compra.metodo_pago if hasattr(compra, "metodo_pago") else "NO DEFINIDO",
            referencia_pago=getattr(compra, "referencia_pago", "") or "",
            efectivo_recibido=getattr(compra, "efectivo_recibido", 0) or 0,
        )

    # Crear líneas solo si no existen
    if factura.lineas.count() == 0:
        for det in compra.detalles.all():
            FacturaDetalle.objects.create(
                factura=factura,
                producto=det.producto,
                cantidad=det.cantidad,
                precio_unitario=det.costo_unitario,
                subtotal=det.cantidad * det.costo_unitario,
                impuesto=(det.cantidad * det.costo_unitario) * Decimal("0.15"),
                total=(det.cantidad * det.costo_unitario) * Decimal("1.15")
            )

    # -----------------------------

    return redirect("compras:detalle", pk=pk)



@login_required
def obtener_precio_producto(request, producto_id):
    try:
        producto = Producto.objects.get(pk=producto_id)
        # Usa costo_promedio o precio_venta dependiendo del contexto
        precio_base = getattr(producto, "costo_promedio", None) or getattr(
            producto, "precio_venta", 0
        )
        return JsonResponse({"costo_unitario": float(precio_base)})
    except Producto.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)


@login_required
@permission_required("compras.change_compra", raise_exception=True)
def anular(request, pk):
    compra = get_object_or_404(Compra, pk=pk)

    # No permitir anular si ya está anulada
    if compra.estado == "ANULADA":
        messages.warning(request, "La compra ya está anulada.")
        return redirect("compras:detalle", pk=pk)

    compra.estado = "ANULADA"
    compra.save(update_fields=["estado"])

    messages.success(request, "Compra anulada correctamente.")
    return redirect("compras:detalle", pk=pk)


@login_required
def api_buscar_productos(request):
    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse({"results": []})

    productos = Producto.objects.filter(
    Q(nombre__icontains=q) | Q(codigo_barras__icontains=q)
    )[:10]

    data = []

    for p in productos:

        stock = MovimientoInventario.objects.filter(producto=p).aggregate(
            total=Coalesce(
                Sum("cantidad", output_field=DecimalField(max_digits=14, decimal_places=3)),
                Value(0, output_field=DecimalField(max_digits=14, decimal_places=3)),
                output_field=DecimalField(max_digits=14, decimal_places=3),
            )
        )["total"] or 0

        data.append({
            "id": p.id,
            "nombre": p.nombre,
            "costo": float(p.costo_promedio or 0),
            "categoria": getattr(p.categoria, "nombre", ""),
            "codigo": p.codigo_barras or "",
            "stock": float(stock),   
        })

    return JsonResponse({"results": data})



@login_required
def api_cargar_lineas(request, pk):
    compra = get_object_or_404(Compra, pk=pk)

    lineas = []
    subtotal = Decimal("0.00")
    impuesto = Decimal("0.00")

    for det in compra.detalles.select_related("producto"):
        producto = det.producto


        stock = MovimientoInventario.objects.filter(producto=producto).aggregate(
            total=Coalesce(
                Sum("cantidad", output_field=DecimalField(max_digits=14, decimal_places=3)),
                Value(0, output_field=DecimalField(max_digits=14, decimal_places=3)),
                output_field=DecimalField(max_digits=14, decimal_places=3),
            )
        )["total"] or 0

        # Calculo de totales
        sub = det.cantidad * det.costo_unitario
        imp = sub * Decimal("0.15")
        tot = sub + imp

        subtotal += sub
        impuesto += imp

        lineas.append({
            "id": det.id,
            "producto": producto.nombre,
            "cantidad": det.cantidad,
            "costo": float(det.costo_unitario),
            "subtotal": float(sub),
            "total": float(tot),
            "categoria": producto.categoria.nombre if producto.categoria else "",
            "codigo": producto.codigo_barras or "",
            "stock": float(stock),  # ← AGREGADO ✔
        })

    # Actualizar totales en la compra
    compra.subtotal = subtotal
    compra.impuesto = impuesto
    compra.total = subtotal + impuesto
    compra.save(update_fields=["subtotal", "impuesto", "total"])

    return JsonResponse({
        "ok": True,
        "lineas": lineas,
        "totales": {
            "subtotal": f"{subtotal:.2f}",
            "impuesto": f"{impuesto:.2f}",
            "total": f"{compra.total:.2f}",
        }
    })




@login_required
def api_agregar_linea(request):
    data = json.loads(request.body)
    compra_id = data.get("compra_id")
    producto_id = data.get("producto_id")

    compra = get_object_or_404(Compra, pk=compra_id)
    producto = get_object_or_404(Producto, pk=producto_id)

    linea, created = CompraDetalle.objects.get_or_create(
        compra=compra,
        producto=producto,
        defaults={"cantidad": 1, "costo_unitario": producto.costo_promedio or 0}
    )

    if not created:
        linea.cantidad += 1
        linea.save()

    return JsonResponse({"ok": True})
@login_required
def api_actualizar_linea(request):
    data = json.loads(request.body)
    linea_id = data.get("linea_id")
    cantidad = data.get("cantidad")

    linea = get_object_or_404(CompraDetalle, pk=linea_id)

    if cantidad <= 0:
        linea.delete()
    else:
        linea.cantidad = cantidad
        linea.save()

    return JsonResponse({"ok": True})
@login_required
def api_eliminar_linea(request):
    data = json.loads(request.body)
    linea_id = data.get("linea_id")

    linea = get_object_or_404(CompraDetalle, pk=linea_id)
    linea.delete()

    return JsonResponse({"ok": True})
@login_required
def api_completar_compra(request, pk):
    compra = get_object_or_404(Compra, pk=pk)

    if compra.estado != "BORRADOR":
        return JsonResponse({"ok": False, "error": "La compra ya está confirmada."})


    data = json.loads(request.body)
    proveedor_id = data.get("proveedor")


    if proveedor_id:
        compra.proveedor_id = proveedor_id
        compra.save(update_fields=["proveedor"])

    # Cambiar estado
    compra.estado = "CONFIRMADA"
    compra.save(update_fields=["estado"])

    # Materializar inventario
    compra.materializar_movimientos()

    # Crear factura COMPRA
    factura, created = Factura.objects.get_or_create(
        tipo="COMPRA",
        numero=f"FC-{compra.id}",
        defaults={
            "proveedor": compra.proveedor,
            "fecha": timezone.now(),
            "subtotal": compra.subtotal,
            "impuesto": compra.impuesto,
            "total": compra.total,
            "creado_por": compra.creado_por,
        }
    )

    # Si ya existía factura pero no tenía creado_por, asignarlo
    if not created and not factura.creado_por:
        factura.creado_por = compra.creado_por
        factura.save(update_fields=["creado_por"])

    # Crear líneas de factura si no existen
    if created and factura.detalles.count() == 0:
        for det in compra.detalles.all():
            FacturaDetalle.objects.create(
                factura=factura,
                producto=det.producto,
                cantidad=det.cantidad,
                precio_unitario=det.costo_unitario,
                subtotal=det.cantidad * det.costo_unitario,
                impuesto=(det.cantidad * det.costo_unitario) * Decimal("0.15"),
                total=(det.cantidad * det.costo_unitario) * Decimal("1.15"),
            )

    return JsonResponse({"ok": True})


@login_required
def api_anular_compra(request, pk):
    compra = get_object_or_404(Compra, pk=pk)

    if compra.estado == "ANULADA":
        return JsonResponse({"ok": False, "error": "La compra ya está anulada."})

    compra.estado = "ANULADA"
    compra.save(update_fields=["estado"])

    return JsonResponse({"ok": True})
