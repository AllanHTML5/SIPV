from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.db.models import Q
from .forms import UsuarioForm, GrupoForm, PasswordChangeForm


# DASHBOARD


@login_required
def auth_dashboard(request):
    return render(request, "authapp/dashboard.html", {
        "total_usuarios": User.objects.count(),
        "total_grupos": Group.objects.count(),
        "total_permisos": Permission.objects.count(),
    })



# USUARIOS


@login_required
def usuarios_lista(request):
    usuarios = User.objects.all().order_by("-id")
    return render(request, "authapp/usuarios/list.html", {"usuarios": usuarios})


@login_required
def usuarios_crear(request):
    form = UsuarioForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        usuario = form.save(commit=False)
        usuario.set_password("Cambiar123*")   
        usuario.save()
        form.save_m2m()

        messages.success(request, "Usuario creado correctamente.")
        return redirect("authapp:usuarios_lista")

    return render(request, "authapp/usuarios/form.html", {
        "form": form,
        "modo": "crear",
    })


@login_required
def usuarios_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UsuarioForm(request.POST or None, instance=usuario)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuario actualizado.")
        return redirect("authapp:usuarios_lista")

    return render(request, "authapp/usuarios/form.html", {
        "form": form,
        "modo": "editar",
        "usuario": usuario
    })


@login_required
def usuarios_eliminar(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        usuario.delete()
        messages.success(request, "Usuario eliminado.")
        return redirect("authapp:usuarios_lista")

    return render(request, "authapp/usuarios/delete.html", {"usuario": usuario})



# CAMBIO DE PASSWORD


@login_required
def usuarios_cambiar_password(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = PasswordChangeForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        usuario.set_password(form.cleaned_data["password"])
        usuario.save()
        messages.success(request, "Contraseña actualizada.")
        return redirect("authapp:usuarios_lista")

    return render(request, "authapp/usuarios/password_modal.html", {
        "form": form,
        "usuario": usuario
    })



# GRUPOS


@login_required
def grupos_lista(request):
    grupos = Group.objects.all().order_by("name")
    return render(request, "authapp/grupos/list.html", {"grupos": grupos})


@login_required
def grupos_crear(request):
    form = GrupoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Grupo creado.")
        return redirect("authapp:grupos_lista")

    return render(request, "authapp/grupos/form.html", {
        "form": form,
        "modo": "crear",
    })


@login_required
def grupos_editar(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    form = GrupoForm(request.POST or None, instance=grupo)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Grupo actualizado.")
        return redirect("authapp:grupos_lista")

    return render(request, "authapp/grupos/form.html", {
        "form": form,
        "modo": "editar",
        "grupo": grupo
    })


@login_required
def grupos_eliminar(request, pk):
    grupo = get_object_or_404(Group, pk=pk)

    if request.method == "POST":
        grupo.delete()
        messages.success(request, "Grupo eliminado.")
        return redirect("authapp:grupos_lista")

    return render(request, "authapp/grupos/delete.html", {"grupo": grupo})




# HTMX Buscador - Usuarios


def usuarios_buscar(request):
    q = request.GET.get("search", "").strip()

    usuarios = User.objects.filter(
        Q(username__icontains=q) |
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q) |
        Q(email__icontains=q)
    )[:25]

    return render(request, "authapp/usuarios/_tabla.html", {"usuarios": usuarios})



# HTMX Buscador - Grupos


def grupos_buscar(request):
    q = request.GET.get("search", "").strip()

    grupos = Group.objects.filter(
        name__icontains=q
    )[:25]

    return render(request, "authapp/grupos/_tabla.html", {"grupos": grupos})


# PERMISOS (solo lectura)


@login_required
def permisos_lista(request):
    permisos = Permission.objects.select_related("content_type").order_by(
        "content_type__app_label",
        "content_type__model",
        "codename"
    )
    return render(request, "authapp/permisos/list.html", {
        "permisos": permisos
    })


@login_required
def permisos_buscar(request):
    q = request.GET.get("search", "").strip()

    permisos = Permission.objects.select_related("content_type").filter(
        Q(name__icontains=q) |
        Q(codename__icontains=q) |
        Q(content_type__app_label__icontains=q) |
        Q(content_type__model__icontains=q)
    )[:40]

    return render(request, "authapp/permisos/_tabla.html", {
        "permisos": permisos
    })


@login_required
def permisos_detalle(request, pk):
    permiso = get_object_or_404(Permission, pk=pk)

    usuarios = permiso.user_set.all()
    grupos = permiso.group_set.all()

    return render(request, "authapp/permisos/detalle.html", {
        "permiso": permiso,
        "usuarios": usuarios,
        "grupos": grupos
    })
