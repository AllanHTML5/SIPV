from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Factura, FacturaDetalle
from maestros.models import Producto, Proveedor
from ventas.models import Cliente
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q


from django.http import HttpResponse
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.dateparse import parse_date

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


import tempfile


def facturas_list(request):

    qs = Factura.objects.select_related("cliente", "proveedor").order_by("-fecha")

    # FILTRO
    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(numero__icontains=q) |
            Q(cliente__nombre__icontains=q) |
            Q(proveedor__nombre__icontains=q)
        )

    # FILTRO: Tipo (VENTA / COMPRA)
    tipo = request.GET.get("tipo")
    if tipo:
        qs = qs.filter(tipo=tipo)

    # FILTRO: Fecha Desde

    desde = request.GET.get("desde")
    if desde:
        fecha_desde = parse_date(desde)
        qs = qs.filter(fecha__date__gte=fecha_desde)


    # FILTRO: Fecha Hasta

    hasta = request.GET.get("hasta")
    if hasta:
        fecha_hasta = parse_date(hasta)
        qs = qs.filter(fecha__date__lte=fecha_hasta)

    return render(request, "facturas/list.html", {
        "facturas": qs,
    })


def factura_detalle(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    lineas = factura.detalles.all()
    return render(request, "facturas/detalle.html", {
        "factura": factura,
        "lineas": lineas
    })


def api_facturas_list(request):
    facturas = Factura.objects.order_by("-fecha").values(
        "id", "tipo", "numero", "fecha", "total"
    )

    return JsonResponse({"ok": True, "facturas": list(facturas)})

@login_required
def factura_pdf(request, pk):
    factura = get_object_or_404(
        Factura.objects.prefetch_related("detalles__producto"), pk=pk
    )

    html = render_to_string("facturas/factura_pdf.html", {
        "factura": factura
    })

    pdf_file = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'inline; filename="Factura-{factura.numero}.pdf"'
    return response



@require_POST
def api_factura_crear(request):
    data = json.loads(request.body)

    tipo = data.get("tipo")
    proveedor_id = data.get("proveedor")
    cliente_id = data.get("cliente")
    numero = data.get("numero")
    lineas = data.get("lineas", [])

    if not numero or not tipo:
        return JsonResponse({"ok": False, "error": "Datos incompletos"}, status=400)

    proveedor = Proveedor.objects.filter(id=proveedor_id).first()
    cliente = Cliente.objects.filter(id=cliente_id).first()

    factura = Factura.objects.create(
        tipo=tipo,
        numero=numero,
        proveedor=proveedor,
        cliente=cliente,
        fecha=timezone.now(),
        subtotal=0,
        impuesto=0,
        total=0
    )

    total_sub = 0
    total_imp = 0

    for item in lineas:
        prod = Producto.objects.get(id=item["producto_id"])
        cant = item["cantidad"]
        precio = prod.precio_venta
        subtotal = cant * precio
        impuesto = subtotal * prod.impuesto

        FacturaLinea.objects.create(
            factura=factura,
            producto=prod,
            cantidad=cant,
            precio_unitario=precio,
            subtotal=subtotal,
            impuesto=impuesto,
            total=subtotal + impuesto
        )

        total_sub += subtotal
        total_imp += impuesto

    factura.subtotal = total_sub
    factura.impuesto = total_imp
    factura.total = total_sub + total_imp
    factura.save()

    return JsonResponse({"ok": True, "factura_id": factura.id})




def factura_venta_pdf(request, pk):
    factura = get_object_or_404(Factura, pk=pk, tipo="VENTA")
    html = render(request, "facturas/factura_venta.html", {"factura": factura})
    pdf = HTML(string=html.content.decode("utf-8")).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="Factura_Venta_{factura.numero}.pdf"'
    return response


def factura_compra_pdf(request, pk):
    factura = get_object_or_404(Factura, pk=pk, tipo="COMPRA")
    html = render(request, "facturas/factura_compra.html", {"factura": factura})
    pdf = HTML(string=html.content.decode("utf-8")).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="Factura_Compra_{factura.numero}.pdf"'
    return response

@login_required
def factura_ticket(request, pk):
    factura = get_object_or_404(
        Factura.objects.prefetch_related("detalles__producto"), pk=pk
    )

    html = render_to_string("facturas/ticket_pdf.html", {
        "factura": factura
    })

    pdf_file = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="Ticket-{factura.numero}.pdf"'
    return response
