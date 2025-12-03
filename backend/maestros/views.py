from rest_framework import viewsets
from .models import Categoria, Proveedor, Producto
from .serializers import CategoriaSerializer, ProveedorSerializer, ProductoSerializer
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required

from .forms import CategoriaForm, ProductoForm, ProveedorForm
from ventas.models import Cliente
from .forms import ClienteForm



@login_required
@permission_required("maestros.view_categoria", raise_exception=True)
def maestros_dashboard(request):
    total_productos = Producto.objects.count()
    total_proveedores = Proveedor.objects.count()
    total_categorias = Categoria.objects.count()
    total_clientes = Cliente.objects.count()   # 👈 NEW

    return render(request, "maestros/dashboard.html", {
        "total_productos": total_productos,
        "total_proveedores": total_proveedores,
        "total_categorias": total_categorias,
        "total_clientes": total_clientes,       # 👈 NEW
    })



# ---------------------------------------------------------
# CATEGORÍAS
# ---------------------------------------------------------

@login_required
@permission_required("maestros.view_categoria", raise_exception=True)
def categorias_lista(request):
    categorias = Categoria.objects.all().order_by("-id")

    return render(request, "maestros/categorias/list.html", {
        "categorias": categorias,
    })


@login_required
@permission_required("maestros.add_categoria", raise_exception=True)
def categorias_crear(request):
    form = CategoriaForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("maestros:categorias_lista")

    return render(request, "maestros/categorias/form.html", {
        "form": form,
        "titulo": "Crear Categoría",
        "boton": "Guardar Categoría",
        "volver_url": "maestros:categorias_lista",
    })


@login_required
@permission_required("maestros.change_categoria", raise_exception=True)
def categorias_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, instance=categoria)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("maestros:categorias_lista")

    return render(request, "maestros/categorias/form.html", {
        "form": form,
        "titulo": "Editar Categoría",
        "boton": "Actualizar Categoría",
        "volver_url": "maestros:categorias_lista",
    })


@login_required
@permission_required("maestros.delete_categoria", raise_exception=True)
def categorias_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == "POST":
        categoria.delete()
        return redirect("maestros:categorias_lista")

    return render(request, "maestros/categorias/delete.html", {
        "objeto": categoria,
        "volver_url": "maestros:categorias_lista",
    })


# ---------------------------------------------------------
# PRODUCTOS
# ---------------------------------------------------------

@login_required
@permission_required("maestros.view_producto", raise_exception=True)
def productos_lista(request):
    query = request.GET.get("search", "").strip()

    productos = Producto.objects.select_related("categoria", "proveedor")

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(codigo_barras__icontains=query) |
            Q(proveedor__nombre__icontains=query) |
            Q(categoria__nombre__icontains=query)
        )

    productos = productos.order_by("-id")

    return render(request, "maestros/productos/list.html", {
        "productos": productos,
        "search": query,
    })


@login_required
@permission_required("maestros.add_producto", raise_exception=True)
def productos_crear(request):
    form = ProductoForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        producto = form.save()
        messages.success(request, f"Producto '{producto.nombre}' creado correctamente.")
        return redirect("maestros:productos_lista")

    return render(request, "maestros/productos/form.html", {
        "form": form,
        "modo": "crear",
    })



@login_required
@permission_required("maestros.change_producto", raise_exception=True)
def productos_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("maestros:productos_lista")

    return render(request, "maestros/productos/form.html", {
        "form": form,
        "titulo": f"Editar Producto — {producto.nombre}",
        "boton": "Actualizar Producto",
        "volver_url": "maestros:productos_lista",
    })


@login_required
@permission_required("maestros.delete_producto", raise_exception=True)
def productos_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        producto.delete()
        return redirect("maestros:productos_lista")

    return render(request, "maestros/productos/delete.html", {
        "objeto": producto,
        "volver_url": "maestros:productos_lista",
    })


@login_required
@permission_required("maestros.view_producto", raise_exception=True)
def productos_detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, "maestros/productos/detalle.html", {
        "producto": producto
    })



@login_required
@permission_required("maestros.view_producto", raise_exception=True)
def productos_buscar(request):
    query = request.GET.get("search", "").strip()

    productos = Producto.objects.filter(
        Q(nombre__icontains=query) |
        Q(codigo_barras__icontains=query) |
        Q(proveedor__nombre__icontains=query) |
        Q(categoria__nombre__icontains=query)
    ).select_related("proveedor", "categoria")[:25]

    return render(request, "maestros/productos/_tabla_resultados.html", {
        "productos": productos
    })




# ---------------------------------------------------------
# PROVEEDORES
# ---------------------------------------------------------

@login_required
@permission_required("maestros.view_proveedor", raise_exception=True)
def proveedores_lista(request):
    proveedores = Proveedor.objects.all().order_by("-id")

    return render(request, "maestros/proveedores/list.html", {
        "proveedores": proveedores
    })


@login_required
@permission_required("maestros.add_proveedor", raise_exception=True)
def proveedores_crear(request):
    form = ProveedorForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("maestros:proveedores_lista")

    return render(request, "maestros/proveedores/form.html", {
        "form": form,
        "titulo": "Crear Proveedor",
        "boton": "Guardar Proveedor",
        "volver_url": "maestros:proveedores_lista",
    })


@login_required
@permission_required("maestros.change_proveedor", raise_exception=True)
def proveedores_editar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=proveedor)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("maestros:proveedores_lista")

    return render(request, "maestros/proveedores/form.html", {
        "form": form,
        "titulo": f"Editar Proveedor — {proveedor.nombre}",
        "boton": "Actualizar Proveedor",
        "volver_url": "maestros:proveedores_lista",
    })


@login_required
@permission_required("maestros.delete_proveedor", raise_exception=True)
def proveedores_eliminar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)

    if request.method == "POST":
        proveedor.delete()
        return redirect("maestros:proveedores_lista")

    return render(request, "maestros/proveedores/delete.html", {
        "objeto": proveedor,
        "volver_url": "maestros:proveedores_lista",
    })



class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer






@login_required
def clientes_lista(request):
    search = request.GET.get("search", "")

    clientes = Cliente.objects.all().order_by("nombre")

    if search:
        clientes = clientes.filter(
            nombre__icontains=search
        )

    return render(request, "maestros/clientes/list.html", {
        "clientes": clientes
    })


@login_required
def clientes_crear(request):
    form = ClienteForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cliente creado correctamente.")
        return redirect("maestros:clientes_lista")

    return render(request, "maestros/clientes/form.html", {
        "form": form,
        "titulo": "Crear Cliente",
        "boton": "Guardar Cliente",
        "volver_url": "maestros:clientes_lista",
    })


@login_required
def clientes_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cliente actualizado.")
        return redirect("maestros:clientes_lista")

    return render(request, "maestros/clientes/form.html", {
        "form": form,
        "titulo": f"Editar Cliente — {cliente.nombre}",
        "boton": "Actualizar Cliente",
        "volver_url": "maestros:clientes_lista",
    })

@login_required
def clientes_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    return render(request, "maestros/clientes/detalle.html", {
        "cliente": cliente
    })


@login_required
def clientes_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        cliente.delete()
        messages.success(request, "Cliente eliminado.")
        return redirect("maestros:clientes_lista")

    return render(request, "maestros/clientes/delete.html", {
        "objeto": cliente
    })
