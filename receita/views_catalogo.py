"""Views administrativas do catalogo de unidades e ingredientes."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from autentica import admin_geral
from logs.utils import registrar_log

from .models import Material, Unidade
from .utils import (
    existe_nome_equivalente,
    normalizar_nome_catalogo,
    ordenar_objetos_por_nome,
)


@admin_geral
def gerenciar_unidades(request):
    if request.method == "POST":
        nome = normalizar_nome_catalogo(request.POST.get("nome_unidade"))
        if nome:
            if existe_nome_equivalente(Unidade, "unidades", nome):
                messages.error(request, "Esta unidade ja esta cadastrada.")
                return redirect("gerenciar_unidades")

            unidade = Unidade(unidades=nome)
            unidade.save()
            registrar_log(
                usuario=request.user,
                acao="CRIAR_UNIDADE",
                id_objeto_alvo=unidade.id,
                nome_objeto=unidade.unidades,
            )
        return redirect("gerenciar_unidades")

    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")
    return render(request, "gerenciar_unidades.html", {"unidades": unidades})


@admin_geral
def editar_unidade(request, pk):
    try:
        unidade = Unidade.objects.get(pk=pk)
        nome_antigo = str(unidade.unidades)
    except Exception:
        messages.error(request, "Unidade nao existe")
        return redirect("gerenciar_unidades")

    if request.method == "POST":
        nome = normalizar_nome_catalogo(request.POST.get("nome_unidade"))
        if nome:
            if existe_nome_equivalente(
                Unidade,
                "unidades",
                nome,
                pk_ignorado=unidade.pk,
            ):
                messages.error(request, "Esta unidade ja esta cadastrada.")
                return redirect("gerenciar_unidades")

            unidade.unidades = nome
            unidade.save()
            registrar_log(
                usuario=request.user,
                acao="EDITAR_UNIDADE",
                id_objeto_alvo=unidade.id,
                nome_objeto=unidade.unidades,
                dados_anteriores={"nome_anterior": nome_antigo},
            )
        return redirect("gerenciar_unidades")

    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")
    return render(request, "gerenciar_unidades.html", {
        "unidades": unidades,
        "unidade_editando": unidade,
    })


@admin_geral
@require_POST
def excluir_unidade(request, pk):
    try:
        unidade = Unidade.objects.get(pk=pk)
    except Exception:
        messages.error(request, "Unidade nao existe")
        return redirect("gerenciar_unidades")

    nome = str(unidade.unidades)
    unidade.delete()
    registrar_log(
        usuario=request.user,
        acao="EXCLUIR_UNIDADE",
        id_objeto_alvo=unidade.id,
        nome_objeto=nome,
    )
    return redirect("gerenciar_unidades")


@admin_geral
def gerenciar_ingredientes(request):
    if request.method == "POST":
        nome = normalizar_nome_catalogo(request.POST.get("nome_ingrediente"))
        if nome:
            if existe_nome_equivalente(Material, "nome", nome):
                messages.error(request, "Este ingrediente ja esta cadastrado.")
                return redirect("gerenciar_ingredientes")

            material = Material.objects.create(nome=nome)
            registrar_log(
                usuario=request.user,
                acao="CRIAR_MATERIAL",
                id_objeto_alvo=material.id,
                nome_objeto=material.nome,
            )
        return redirect("gerenciar_ingredientes")

    ingredientes = ordenar_objetos_por_nome(Material.objects.all(), "nome")
    return render(request, "gerenciar_ingredientes.html", {"ingredientes": ingredientes})


@admin_geral
def editar_ingrediente(request, pk):
    try:
        ingrediente = Material.objects.get(pk=pk)
    except Exception:
        messages.error(request, "Ingrediente nao existe")
        return redirect("gerenciar_ingredientes")

    if request.method == "POST":
        nome = normalizar_nome_catalogo(request.POST.get("nome_ingrediente"))
        if nome:
            if existe_nome_equivalente(
                Material,
                "nome",
                nome,
                pk_ignorado=ingrediente.pk,
            ):
                messages.error(request, "Este ingrediente ja esta cadastrado.")
                return redirect("gerenciar_ingredientes")

            nome_antigo = ingrediente.nome
            ingrediente.nome = nome
            ingrediente.save()
            registrar_log(
                usuario=request.user,
                acao="EDITAR_MATERIAL",
                id_objeto_alvo=ingrediente.id,
                nome_objeto=ingrediente.nome,
                dados_anteriores={"nome": nome_antigo},
            )
        return redirect("gerenciar_ingredientes")

    ingredientes = ordenar_objetos_por_nome(Material.objects.all(), "nome")
    return render(request, "gerenciar_ingredientes.html", {
        "ingredientes": ingredientes,
        "ingrediente_editando": ingrediente,
    })


@admin_geral
@require_POST
def excluir_ingrediente(request, pk):
    try:
        ingrediente = Material.objects.get(pk=pk)
    except Exception:
        messages.error(request, "Ingrediente nao existe")
        return redirect("gerenciar_ingredientes")

    nome = ingrediente.nome
    ingrediente_id = ingrediente.id
    ingrediente.delete()
    registrar_log(
        usuario=request.user,
        acao="EXCLUIR_MATERIAL",
        id_objeto_alvo=ingrediente_id,
        nome_objeto=nome,
    )
    return redirect("gerenciar_ingredientes")
