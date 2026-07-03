from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from usuarios.models import Grupo


def usuario(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Faça login para continuar.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_grupo(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Faça login para continuar.")
            return redirect("login")

        if request.user.is_staff:
            return view_func(request, *args, **kwargs)

        if Grupo.objects.filter(administradores=request.user).exists():
            return view_func(request, *args, **kwargs)

        messages.error(request, "Você precisa ser administrador de grupo para acessar esta área.")
        return redirect("home")
    return wrapper


def admin_geral(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Faça login para continuar.")
            return redirect("login")

        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Acesso restrito ao administrador geral.")
        return redirect("home")
    return wrapper