from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from common.permisos import permisos_modulos


@login_required
def home_dashboard(request):
    return render(request, "home/dashboard.html")
