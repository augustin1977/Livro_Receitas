from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from usuarios.models import Grupo


def usuario(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Faca login para continuar.")
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_grupo(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Faca login para continuar.")
            return redirect("login")

        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        grupo_id = kwargs.get("grupo_id")
        if grupo_id and Grupo.objects.filter(
            id=grupo_id,
            administradores=request.user
        ).exists():
            return view_func(request, *args, **kwargs)

        messages.error(request, "Voce precisa ser administrador deste grupo.")
        return redirect("home")

    return wrapper


def admin_geral(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Faca login para continuar.")
            return redirect("login")

        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Acesso restrito ao administrador geral.")
        return redirect("home")

    return wrapper
