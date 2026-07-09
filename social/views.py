from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from autentica import usuario
from logs.utils import registrar_log
from receita.selectors import receitas_visiveis_para

from .models import Comentario


def redirecionar_para_receita(receita_id):
    base_url = reverse("mostrar_receita")
    query_string = urlencode({"receita": receita_id})
    return redirect(f"{base_url}?{query_string}")


@usuario
def adicionar_comentario(request, receita_id):
    if request.method != "POST":
        return redirect("mostrar_receitas")

    receita = receitas_visiveis_para(request.user).filter(id=receita_id).first()
    if not receita:
        messages.error(request, "Receita nao encontrada ou sem permissao.")
        return redirect("mostrar_receitas")

    texto = request.POST.get("texto")
    if texto:
        comentario = Comentario.objects.create(
            receita=receita,
            usuario=request.user,
            texto=texto
        )
        registrar_log(
            usuario=request.user,
            acao="CRIAR_COMENTARIO",
            id_objeto_alvo=comentario.id,
            nome_objeto=receita.nome,
            dados_novos={"texto": texto, "receita_id": receita.id},
        )

    return redirecionar_para_receita(receita_id)


@usuario
def editar_comentario(request, comentario_id):
    if request.method != "POST":
        return redirect("mostrar_receitas")

    try:
        comentario = Comentario.objects.select_related("receita", "usuario").get(
            id=comentario_id
        )
    except Comentario.DoesNotExist:
        messages.error(request, "O comentario que voce tentou editar nao existe.")
        return redirect("mostrar_receitas")

    receita_visivel = receitas_visiveis_para(request.user).filter(
        id=comentario.receita_id
    ).exists()
    if not receita_visivel:
        messages.error(request, "Voce nao tem permissao para acessar esta receita.")
        return redirect("mostrar_receitas")

    if comentario.usuario != request.user:
        messages.error(request, "Voce nao tem permissao para editar este comentario.")
        return redirecionar_para_receita(comentario.receita_id)

    novo_texto = request.POST.get("texto")
    if novo_texto:
        texto_anterior = comentario.texto
        comentario.texto = novo_texto
        comentario.save()
        registrar_log(
            usuario=request.user,
            acao="EDITAR_COMENTARIO",
            id_objeto_alvo=comentario.id,
            nome_objeto=comentario.receita.nome,
            dados_anteriores={
                "texto": texto_anterior,
                "receita_id": comentario.receita_id,
            },
            dados_novos={
                "texto": novo_texto,
                "receita_id": comentario.receita_id,
            },
        )

    return redirecionar_para_receita(comentario.receita_id)


@usuario
@require_POST
def excluir_comentario(request, comentario_id):
    try:
        comentario = Comentario.objects.select_related("receita", "usuario").get(
            id=comentario_id
        )
    except Comentario.DoesNotExist:
        messages.error(request, "O comentario que voce tentou excluir nao existe.")
        return redirect("mostrar_receitas")

    receita_visivel = receitas_visiveis_para(request.user).filter(
        id=comentario.receita_id
    ).exists()
    if not receita_visivel:
        messages.error(request, "Voce nao tem permissao para acessar esta receita.")
        return redirect("mostrar_receitas")

    e_autor_comentario = comentario.usuario == request.user
    e_dono_receita = comentario.receita.usuario == request.user
    e_admin = request.user.is_staff or request.user.is_superuser

    if not (e_autor_comentario or e_dono_receita or e_admin):
        messages.error(request, "Voce nao tem permissao para excluir este comentario.")
        return redirecionar_para_receita(comentario.receita_id)

    receita_id = comentario.receita_id
    comentario_id = comentario.id
    texto_anterior = comentario.texto
    nome_receita = comentario.receita.nome
    comentario.delete()
    registrar_log(
        usuario=request.user,
        acao="EXCLUIR_COMENTARIO",
        id_objeto_alvo=comentario_id,
        nome_objeto=nome_receita,
        dados_anteriores={"texto": texto_anterior, "receita_id": receita_id},
    )

    messages.success(request, "Comentario removido com sucesso.")
    return redirecionar_para_receita(receita_id)
