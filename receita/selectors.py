from django.db.models import Q

from .models import Receita


NOME_GRUPO_TECNICO_SEM_FAMILIA = "Sem_Familia"


def grupos_sociais_do_usuario(usuario):
    return usuario.grupos.exclude(nome=NOME_GRUPO_TECNICO_SEM_FAMILIA)


def receitas_visiveis_para(usuario):
    grupos_usuario = grupos_sociais_do_usuario(usuario)

    return Receita.objects.filter(
        Q(usuario=usuario) |
        Q(usuario__grupos__in=grupos_usuario)
    ).distinct()
