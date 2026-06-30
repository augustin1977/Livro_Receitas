from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from usuarios.models import Grupo 

def usuario_obrigatorio(view_func):
    """Garante apenas que o usuário esteja logado no sistema."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/') 
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_geral_obrigatorio(view_func):
    """Garante que o usuário seja um Administrador Geral (is_staff)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        
        if not request.user.is_staff:
            messages.error(request, "Acesso restrito para Administradores Gerais.")
            return redirect('/receita/home/')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_grupo_obrigatorio(view_func):
    """Garante estritamente que o usuário administra pelo menos um grupo."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
            
        # Verifica se o usuário logado está associado como administrador em algum grupo
        se_administra = Grupo.objects.filter(administadores=request.user).exists()
        if not se_administra:
            messages.error(request, "Acesso restrito para Administradores de Grupo.")
            return redirect('/receita/home/')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view