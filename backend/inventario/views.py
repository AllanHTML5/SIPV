# inventario/views.py
from datetime import timedelta
import csv

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import (
    Sum, Case, When, F, Value, Q, DecimalField, ExpressionWrapper
)
from django.db.models.functions import Coalesce, TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

from maestros.models import Producto, Categoria, Proveedor
from .models import Existencia, MovimientoInventario
from .forms import AjusteInventarioForm
from compras.models import CompraDetalle
from ventas.models import VentaDetalle

from common.permisos import permisos_modulos





DEC_QTY = DecimalField(max_digits=14, decimal_places=3)


def annotate_stock(qs_productos):
    """
    Suma/resta movimientos por tipo para obtener 'stock' como anotación.
    """
    signed_qty = Case(
        When(movimientos__tipo__in=['ENTRADA', 'AJUSTE_POS'], then=F('movimientos__cantidad')),
        When(
            movimientos__tipo__in=['SALIDA', 'AJUSTE_NEG'],
            then=ExpressionWrapper(-F('movimientos__cantidad'), output_field=DEC_QTY),
        ),
        default=Value(0),
        output_field=DEC_QTY,
    )
    return qs_productos.annotate(
        stock=Coalesce(Sum(signed_qty), Value(0, output_field=DEC_QTY), output_field=DEC_QTY)
    )


@login_required
def dashboard_data(request):
    from decimal import Decimal
    dec3 = DecimalField(max_digits=14, decimal_places=3)

    # Últimos 30 días
    hoy = timezone.now().date()
    desde = hoy - timedelta(days=29)

    labels = [(desde + timedelta(days=i)) for i in range(30)]
    labels_str = [d.strftime("%Y-%m-%d") for d in labels]


    # COMPRAS POR DÍA

    compras_qs = (
        CompraDetalle.objects
        .filter(
            compra__fecha__gte=desde,
            compra__fecha__lte=hoy + timedelta(days=1)
        )
        .annotate(d=TruncDate("compra__fecha"))
        .values("d")
        .annotate(
            total=Coalesce(
                Sum("cantidad", output_field=dec3),
                Value(0, output_field=dec3)
            )
        )
        .order_by("d")
    )

    compras_map = {
        row["d"].strftime("%Y-%m-%d"): float(row["total"])
        for row in compras_qs
    }
    compras_series = [compras_map.get(d, 0.0) for d in labels_str]


    # VENTAS POR DÍA 

    ventas_qs = (
        VentaDetalle.objects
        .filter(
            venta__creado__gte=desde,
            venta__creado__lte=hoy + timedelta(days=1) 
        )
        .annotate(d=TruncDate("venta__creado"))
        .values("d")
        .annotate(
            total=Coalesce(
                Sum("cantidad", output_field=dec3),
                Value(0, output_field=dec3)
            )
        )
        .order_by("d")
    )

    ventas_map = {
        row["d"].strftime("%Y-%m-%d"): float(row["total"])
        for row in ventas_qs
    }
    ventas_series = [ventas_map.get(d, 0.0) for d in labels_str]


    # TOP PRODUCTOS VENDIDOS

    top_qs = (
        VentaDetalle.objects
        .values("producto__nombre")
        .annotate(
            total=Coalesce(
                Sum("cantidad", output_field=dec3),
                Value(0, output_field=dec3)
            )
        )
        .order_by("-total")[:10]
    )

    top_labels = [row["producto__nombre"] for row in top_qs]
    top_values = [float(row["total"]) for row in top_qs]

    # STOCK POR CATEGORÍA



    stock_cat_qs = (
        Existencia.objects
        .select_related("producto__categoria")
        .values("producto__categoria__nombre")
        .annotate(
            total=Coalesce(
                Sum("cantidad", output_field=dec3),
                Value(0, output_field=dec3)
            )
        )
        .order_by("-total")
    )

    stock_cat_labels = [
        row["producto__categoria__nombre"] or "Sin categoría"
        for row in stock_cat_qs
    ]
    stock_cat_values = [float(row["total"]) for row in stock_cat_qs]


    # TOTALES

    total_items = Producto.objects.filter(activo=True).count()
    con_alerta = Existencia.objects.filter(
        producto__activo=True,
        cantidad__lt=F("producto__stock_minimo")
    ).count()

    return JsonResponse({
        "compras_ventas": {
            "labels": labels_str,
            "compras": compras_series,
            "ventas": ventas_series,
        },
        "top_vendidos": {
            "labels": top_labels,
            "values": top_values,
        },
        "stock_por_categoria": {
            "labels": stock_cat_labels,
            "values": stock_cat_values,
        },
        "totales": {
            "total_items": total_items,
            "con_alerta": con_alerta,
        },
    })




@login_required
def dashboard(request):
    # Base sin anotar 
    qs_base = Producto.objects.filter(activo=True)

    # QS con la anotación de stock
    qs_stock = annotate_stock(qs_base)

    # Usa SIEMPRE el queryset anotado cuando referencies "stock"
    bajo_min = qs_stock.filter(stock__lt=F('stock_minimo')).select_related('categoria')[:10]
    total_items = qs_base.count()  
    con_alerta = qs_stock.filter(stock__lt=F('stock_minimo')).count()

    # Movimientos recientes
    movs = MovimientoInventario.objects.select_related('producto').order_by('-creado')[:10]


    exist_qs = Existencia.objects.select_related('producto').filter(producto__activo=True)

    from decimal import Decimal
    inv_total_unidades = exist_qs.aggregate(
        total=Coalesce(Sum('cantidad', output_field=DEC_QTY), Value(0, output_field=DEC_QTY))
    )['total'] or 0

    inv_valor_costo = Decimal('0')
    inv_valor_pot = Decimal('0')
    for e in exist_qs:
        qty = e.cantidad or 0
        p = e.producto
        costo = getattr(p, 'costo_promedio', None) or Decimal('0')
        precio = getattr(p, 'precio_venta', None) or Decimal('0')
        inv_valor_costo += qty * costo
        inv_valor_pot += qty * precio

    agotados = exist_qs.filter(cantidad__lte=0).count()
    bajos = exist_qs.filter(cantidad__gt=0, cantidad__lt=F('producto__stock_minimo')).count()


    ctx = {
        'total_items': total_items,
        'con_alerta': con_alerta,
        'bajo_min': bajo_min,
        'movs': movs,

        'inv_total_unidades': inv_total_unidades,
        'inv_valor_costo': inv_valor_costo,
        'inv_valor_pot': inv_valor_pot,
        'inv_agotados': agotados,
        'inv_bajos': bajos,
    }


    return render(request, 'inventario/dashboard.html', ctx)



@login_required
def stock_list(request):
    q = request.GET.get('q', '').strip()
    proveedor = request.GET.get("proveedor")
    precio_min = request.GET.get("precio_min")
    precio_max = request.GET.get("precio_max")
    stock_min = request.GET.get("stock_min")
    stock_max = request.GET.get("stock_max")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    ordering = request.GET.get("ordering", "nombre")
    export = request.GET.get("export")

    productos = Producto.objects.filter(activo=True).select_related("proveedor")

    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) |
            Q(codigo_barras__icontains=q)
        )

    if proveedor:
        productos = productos.filter(proveedor_id=proveedor)

    if precio_min:
        productos = productos.filter(precio_venta__gte=precio_min)

    if precio_max:
        productos = productos.filter(precio_venta__lte=precio_max)

    if fecha_desde:
        productos = productos.filter(creado__date__gte=fecha_desde)

    if fecha_hasta:
        productos = productos.filter(creado__date__lte=fecha_hasta)


    productos = annotate_stock(productos)

    if stock_min:
        productos = productos.filter(stock__gte=stock_min)

    if stock_max:
        productos = productos.filter(stock__lte=stock_max)

    productos = productos.order_by(ordering)


    if export == 'csv':
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="stock.csv"'
        writer = csv.writer(resp)
        writer.writerow(['Producto', 'Codigo', 'Proveedor', 'Precio', 'Min', 'Stock'])
        for p in productos:
            writer.writerow([
                p.nombre,
                getattr(p, 'codigo_barras', '') or '',
                p.proveedor.nombre if p.proveedor else '',
                p.precio_venta,
                p.stock_minimo,
                p.stock or 0
            ])
        return resp

    if export == 'pdf':

        html = render_to_string('inventario/reports/stock_pdf.html', {
            'productos': productos,
            'q': q,
            'ordering': ordering,
            'generado': timezone.now(),
            'usuario': request.user.get_full_name() or request.user.username,
        })

        PDF_CSS = """
            @page {
                size: A4;
                margin: 20mm;
            }

            @page {
                @bottom-center {
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 9px;
                    color: #475569;
                }
            }

            body {
                font-family: DejaVu Sans, sans-serif;
                font-size: 12px;
                color: #0f172a;
            }

            h1 {
                font-size: 20px;
                margin-bottom: 4px;
                color: #1e293b;
            }

            h2 {
                font-size: 13px;
                margin-top: 2px;
                font-weight: normal;
                color: #475569;
            }

            .header {
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }

            .meta {
                margin-top: 4px;
                color: #475569;
                font-size: 11px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }

            th {
                background: #f1f5f9;
                padding: 8px 6px;
                border-bottom: 1px solid #cbd5e1;
                font-weight: 600;
                font-size: 11px;
                color: #334155;
                text-align: left;
            }

            td {
                padding: 8px 6px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 11px;
            }

            td.num {
                text-align: right;
                font-variant-numeric: tabular-nums;
            }

            .footer-space {
                height: 20px;
            }
        """

        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(
            stylesheets=[CSS(string=PDF_CSS)]
        )

        resp = HttpResponse(pdf, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="stock.pdf"'
        return resp


    paginator = Paginator(productos, 20)
    page = paginator.get_page(request.GET.get('page') or 1)

    proveedores = Proveedor.objects.filter(estado=True).order_by("nombre")

    return render(request, 'inventario/stock_list.html', {
        'page': page,
        'q': q,
        'ordering': ordering,
        'proveedores': proveedores,
    })



def stock_table_partial(request):
    q = request.GET.get("q", "").strip()
    proveedor = request.GET.get("proveedor")
    precio_min = request.GET.get("precio_min")
    precio_max = request.GET.get("precio_max")
    stock_min = request.GET.get("stock_min")
    stock_max = request.GET.get("stock_max")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    ordering = request.GET.get("ordering", "nombre")

    productos = Producto.objects.filter(activo=True).select_related(
        "existencia", "proveedor"
    )

 
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) |
            Q(codigo_barras__icontains=q)
        )

    if proveedor:
        productos = productos.filter(proveedor_id=proveedor)

    if precio_min:
        productos = productos.filter(precio_venta__gte=precio_min)

    if precio_max:
        productos = productos.filter(precio_venta__lte=precio_max)

    if stock_min:
        productos = productos.filter(existencia__cantidad__gte=stock_min)

    if stock_max:
        productos = productos.filter(existencia__cantidad__lte=stock_max)

    if fecha_desde:
        productos = productos.filter(creado__date__gte=fecha_desde)

    if fecha_hasta:
        productos = productos.filter(creado__date__lte=fecha_hasta)

 
    from inventario.utils import annotate_stock
    productos = annotate_stock(productos).order_by(ordering)

    paginator = Paginator(productos, 20)
    page = paginator.get_page(request.GET.get("page") or 1)

    return render(request, "inventario/partials/stock_table_partial.html", {
        "page": page
    })


@login_required
def movimientos(request):
    productos = Producto.objects.filter(activo=True).order_by("nombre")
    proveedores = Proveedor.objects.filter(estado=True).order_by("nombre")

    return render(request, "inventario/movimientos.html", {
        "productos": productos,
        "proveedores": proveedores,
    })



@login_required
def movimientos_partial(request):
    print("HTMX PARAMS:", request.GET)

    q = request.GET.get("q", "").strip()
    producto_id = request.GET.get("producto")
    proveedor = request.GET.get("proveedor")
    tipo = request.GET.get("tipo")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")

    movs = MovimientoInventario.objects.select_related(
        "producto", "producto__proveedor"
    )

    if q:
        movs = movs.filter(
            Q(producto__nombre__icontains=q) |
            Q(motivo__icontains=q) |
            Q(referencia__icontains=q)
        )

    if producto_id:
        movs = movs.filter(producto_id=producto_id)

    if proveedor:
        movs = movs.filter(producto__proveedor_id=proveedor)

    if tipo:
        movs = movs.filter(tipo=tipo)

    if fecha_desde:
        movs = movs.filter(creado__date__gte=fecha_desde)

    if fecha_hasta:
        movs = movs.filter(creado__date__lte=fecha_hasta)

    movs = movs.order_by("-creado")[:300]

    return render(request, "inventario/partials/movimientos_table.html", {
        "movimientos": movs
    })



@login_required
@permission_required('inventario.add_movimientoinventario', raise_exception=True)
@require_http_methods(["GET", "POST"])
def ajuste_modal(request):
    if request.method == "POST":
        form = AjusteInventarioForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Firma la cantidad según el tipo seleccionado
            signo = 1 if cd['tipo'] == 'AJUSTE_POS' else -1
            cantidad = cd['cantidad'] if signo == 1 else -cd['cantidad']

            # Usa el tipo REAL del formulario 
            mi = MovimientoInventario(
                producto=cd['producto'],
                tipo=cd['tipo'],
                cantidad=cantidad,
            )

            # motivo -> referencia o motivo, según exista en tu modelo
            if hasattr(mi, 'referencia'):
                mi.referencia = cd.get('motivo', '')
            elif hasattr(mi, 'motivo'):
                mi.motivo = cd.get('motivo', '')

            # usuario si existe el campo en el modelo
            if hasattr(mi, 'usuario'):
                mi.usuario = request.user

            mi.save()

            resp = HttpResponse("")
            resp["HX-Refresh"] = "true"  
            return resp

        # Si no es válido, re-render del partial con errores
        return render(request, "inventario/partials/ajuste_modal.html", {"form": form})

    # GETas
    form = AjusteInventarioForm()
    return render(request, "inventario/partials/ajuste_modal.html", {"form": form})


@login_required
@require_http_methods(["POST"])
@permission_required('inventario.add_movimientoinventario', raise_exception=True)
def ajuste_crear(request):
    form = AjusteInventarioForm(request.POST)
    if form.is_valid():
        form.save(request.user)
        resp = render(request, 'inventario/partials/ajuste_success.html', {})
        resp['X-Toast'] = "Ajuste registrado"
        return resp
    return render(request, 'inventario/partials/ajuste_modal.html', {'form': form}, status=400)

def producto_autocomplete(request):
    q = request.GET.get("producto_search", "").strip()

    productos = Producto.objects.filter(
        nombre__icontains=q
    ).order_by("nombre")[:20]

    return render(request, "inventario/partials/producto_autocomplete.html", {
        "productos": productos
    })
