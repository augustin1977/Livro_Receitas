"""Views e helpers da pagina inicial e do feed de atividades."""

from django.shortcuts import render
from django.urls import reverse

from autentica import usuario
from logs.models import LogAtividade
from usuarios.models import ConviteGrupo, Grupo, Usuario

from .models import Receita
from .selectors import grupos_sociais_do_usuario, receitas_visiveis_para


ACOES_JORNAL_HOME = {
    "CRIAR_RECEITA",
    "COPIAR_RECEITA",
    "EDITAR_RECEITA",
    "ADICIONAR_INGREDIENTE_RECEITA",
    "EDITAR_INGREDIENTE_RECEITA",
    "REMOVER_INGREDIENTE_RECEITA",
    "CRIAR_COMENTARIO",
    "EDITAR_COMENTARIO",
    "EXCLUIR_COMENTARIO",
    "FAVORITAR",
    "CRIAR_GRUPO",
    "ENVIAR_CONVITE_GRUPO",
    "ACEITAR_CONVITE_GRUPO",
}

ACOES_RECEITA_HOME = {
    "CRIAR_RECEITA",
    "COPIAR_RECEITA",
    "EDITAR_RECEITA",
    "ADICIONAR_INGREDIENTE_RECEITA",
    "EDITAR_INGREDIENTE_RECEITA",
    "REMOVER_INGREDIENTE_RECEITA",
    "FAVORITAR",
}

ACOES_COMENTARIO_HOME = {
    "CRIAR_COMENTARIO",
    "EDITAR_COMENTARIO",
    "EXCLUIR_COMENTARIO",
}

ACOES_GRUPO_HOME = {
    "CRIAR_GRUPO",
    "ENVIAR_CONVITE_GRUPO",
    "ACEITAR_CONVITE_GRUPO",
}


def usuarios_da_rede_home_ids(usuario_atual):
    """A home so mostra atividade de quem compartilha grupo social real."""
    grupos_usuario = grupos_sociais_do_usuario(usuario_atual)
    usuarios_ids = set(
        Usuario.objects.filter(grupos__in=grupos_usuario).values_list("id", flat=True)
    )
    usuarios_ids.add(usuario_atual.id)
    return usuarios_ids


def url_receita(receita_id):
    """Monta a URL historica da tela de detalhe que recebe o id por query string."""
    return f"{reverse('mostrar_receita')}?receita={receita_id}"


def texto_jornal_home(log, nome):
    """Transforma logs de auditoria em textos curtos para o feed da home."""
    usuario_nome = log.usuario.username if log.usuario else "Alguem"

    textos = {
        "CRIAR_RECEITA": f"{usuario_nome} publicou a receita '{nome}'",
        "COPIAR_RECEITA": f"{usuario_nome} copiou a receita '{nome}'",
        "EDITAR_RECEITA": f"{usuario_nome} editou a receita '{nome}'",
        "ADICIONAR_INGREDIENTE_RECEITA": f"{usuario_nome} mexeu nos ingredientes da receita '{nome}'",
        "EDITAR_INGREDIENTE_RECEITA": f"{usuario_nome} mexeu nos ingredientes da receita '{nome}'",
        "REMOVER_INGREDIENTE_RECEITA": f"{usuario_nome} mexeu nos ingredientes da receita '{nome}'",
        "CRIAR_COMENTARIO": f"{usuario_nome} comentou na receita '{nome}'",
        "EDITAR_COMENTARIO": f"{usuario_nome} atualizou um comentario na receita '{nome}'",
        "EXCLUIR_COMENTARIO": f"{usuario_nome} removeu um comentario da receita '{nome}'",
        "FAVORITAR": f"{usuario_nome} favoritou a receita '{nome}'",
        "CRIAR_GRUPO": f"{usuario_nome} criou o grupo '{nome}'",
        "ENVIAR_CONVITE_GRUPO": f"{usuario_nome} movimentou o grupo '{nome}'",
        "ACEITAR_CONVITE_GRUPO": f"{usuario_nome} entrou no grupo '{nome}'",
    }
    return textos.get(log.acao, log.texto_jornal)


def receita_id_do_log(log):
    """Descobre a receita associada a um log de receita ou comentario."""
    if log.acao in ACOES_RECEITA_HOME:
        return log.id_objeto_alvo

    if log.acao in ACOES_COMENTARIO_HOME:
        dados = log.dados_novos or log.dados_anteriores or {}
        return dados.get("receita_id")

    return None


def montar_atividade_home(log, receitas_visiveis_ids, grupos_visiveis_ids):
    """Monta uma atividade clicavel somente se o alvo ainda for visivel ao usuario."""
    if log.acao in ACOES_RECEITA_HOME or log.acao in ACOES_COMENTARIO_HOME:
        receita_id = receita_id_do_log(log)
        if not receita_id or receita_id not in receitas_visiveis_ids:
            return None

        receita = Receita.objects.filter(id=receita_id).first()
        if not receita:
            return None

        url = url_receita(receita_id)
        nome = receita.nome

    elif log.acao in ACOES_GRUPO_HOME:
        grupo_id = log.id_objeto_alvo
        if not grupo_id or grupo_id not in grupos_visiveis_ids:
            return None

        grupo = Grupo.objects.filter(id=grupo_id).first()
        if not grupo:
            return None

        url = reverse("gerenciar_grupo", args=[grupo_id])
        nome = grupo.nome
    else:
        return None

    return {
        "texto": texto_jornal_home(log, nome),
        "url": url,
        "data": log.data,
        "acao": log.acao,
    }


def atividades_home_para(usuario_atual, limite=5):
    """Busca as atividades recentes da rede do usuario respeitando visibilidade."""
    usuarios_rede_ids = usuarios_da_rede_home_ids(usuario_atual)
    receitas_visiveis_ids = set(
        receitas_visiveis_para(usuario_atual).values_list("id", flat=True)
    )
    grupos_visiveis_ids = set(
        grupos_sociais_do_usuario(usuario_atual).values_list("id", flat=True)
    )

    atividades = []
    logs = LogAtividade.objects.select_related("usuario").filter(
        acao__in=ACOES_JORNAL_HOME,
        usuario_id__in=usuarios_rede_ids,
    )[:50]

    for log in logs:
        atividade = montar_atividade_home(
            log,
            receitas_visiveis_ids,
            grupos_visiveis_ids,
        )
        if atividade:
            atividades.append(atividade)

        if len(atividades) == limite:
            break

    return atividades


@usuario
def home(request):
    """Exibe os indicadores, ultimas receitas e atividades visiveis ao usuario."""
    usuario_atual = request.user

    total_receitas_pessoais = Receita.objects.filter(usuario=usuario_atual).count()

    grupos_usuario = Grupo.objects.filter(membros=usuario_atual)
    total_grupos = grupos_usuario.count()

    total_convites = ConviteGrupo.objects.filter(usuario_convidado=usuario_atual).count()

    total_receitas_grupos = receitas_visiveis_para(usuario_atual).exclude(
        usuario=usuario_atual
    ).count()

    ultimas_receitas = receitas_visiveis_para(usuario_atual).select_related(
        "usuario",
        "criador_original",
    ).order_by("-data_ultima_modificacao")[:5]

    atividades_jornal = atividades_home_para(usuario_atual)

    return render(request, "home.html", {
        "total_receitas_pessoais": total_receitas_pessoais,
        "total_receitas_grupos": total_receitas_grupos,
        "total_grupos": total_grupos,
        "total_convites": total_convites,
        "ultimas_receitas": ultimas_receitas,
        "atividades_jornal": atividades_jornal,
    })
