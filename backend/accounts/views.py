from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")


    next_url = (request.POST.get("next") or request.GET.get("next") or "/").strip() or "/"

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "accounts/login.html", {"next": next_url})


def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")
