from django.db.models import Q

from .models import Receita


def receitas_visiveis_para(usuario):
    grupos_usuario = usuario.grupos.all()

    return Receita.objects.filter(
        Q(usuario=usuario) |
        Q(usuario__grupos__in=grupos_usuario)
    ).distinct()
