"""Views de grupos, convites e administracao de membros."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from autentica import admin_grupo, usuario
from logs.utils import registrar_log

from .models import ConviteGrupo, Grupo, Usuario
from .permissions import usuario_administra_grupo


@usuario
def cadastrar_grupo(request):
    if request.method == "POST":
        nome_grupo = request.POST.get("nome", "").strip()

        if not nome_grupo:
            messages.error(request, "O nome do grupo nao pode ficar em branco.")
            return redirect("cadastrar_grupo")

        if Grupo.objects.filter(nome=nome_grupo).exists():
            messages.error(request, "Ja existe um grupo com este nome.")
            return redirect("cadastrar_grupo")

        novo_grupo = Grupo.objects.create(nome=nome_grupo)
        novo_grupo.membros.add(request.user)
        novo_grupo.administradores.add(request.user)
        registrar_log(
            usuario=request.user,
            acao="CRIAR_GRUPO",
            id_objeto_alvo=novo_grupo.id,
            nome_objeto=novo_grupo.nome,
        )

        messages.success(
            request,
            f"Grupo '{nome_grupo}' criado com sucesso! Agora voce pode adicionar membros.",
        )
        return redirect("gerenciar_grupo", grupo_id=novo_grupo.id)

    return render(request, "cadastrar_grupo.html")


@usuario
def gerenciar_grupo(request, grupo_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo desejado.")
        return redirect("meus_grupos_administrados")

    if request.user not in grupo.membros.all():
        messages.error(request, "Voce nao tem permissao para acessar este grupo.")
        return redirect("meus_grupos_administrados")

    return render(request, "gerenciar_grupo.html", {"grupo": grupo})


@usuario
def adicionar_membro(request, grupo_id):
    if request.method != "POST":
        return redirect("meus_grupos_administrados")

    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Exception:
        messages.error(request, "Grupo nao encontrado.")
        return redirect("meus_grupos_administrados")

    if not usuario_administra_grupo(request, grupo):
        messages.error(request, "Permissao negada.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    busca = request.POST.get("busca", "").strip()

    try:
        usuario_alvo = Usuario.objects.get(username=busca)
    except Usuario.DoesNotExist:
        try:
            usuario_alvo = Usuario.objects.get(email=busca)
        except Usuario.DoesNotExist:
            messages.error(request, f"Usuario '{busca}' nao encontrado.")
            return redirect("gerenciar_grupo", grupo_id=grupo.id)

    if usuario_alvo in grupo.membros.all():
        messages.warning(request, f"'{usuario_alvo.username}' ja faz parte deste grupo.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    if ConviteGrupo.objects.filter(grupo=grupo, usuario_convidado=usuario_alvo).exists():
        messages.warning(
            request,
            f"Ja existe um convite pendente para '{usuario_alvo.username}'.",
        )
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    convite = ConviteGrupo.objects.create(grupo=grupo, usuario_convidado=usuario_alvo)
    registrar_log(
        usuario=request.user,
        acao="ENVIAR_CONVITE_GRUPO",
        id_objeto_alvo=convite.id,
        nome_objeto=grupo.nome,
        dados_anteriores={"usuario_convidado_id": usuario_alvo.id},
    )
    messages.success(
        request,
        f"Convite enviado para '{usuario_alvo.username}'. Aguardando aprovacao dele.",
    )
    return redirect("gerenciar_grupo", grupo_id=grupo.id)


@usuario
def meus_convites(request):
    convites = ConviteGrupo.objects.filter(
        usuario_convidado=request.user
    ).order_by("-data_envio")
    return render(request, "meus_convites.html", {"convites": convites})


@usuario
@require_POST
def responder_convite(request, convite_id, acao):
    try:
        convite = ConviteGrupo.objects.get(id=convite_id, usuario_convidado=request.user)
    except Exception:
        messages.error(request, "Convite nao encontrado ou ja processado.")
        return redirect("meus_convites")

    if acao == "aceitar":
        convite.grupo.membros.add(request.user)
        registrar_log(
            usuario=request.user,
            acao="ACEITAR_CONVITE_GRUPO",
            id_objeto_alvo=convite.grupo.id,
            nome_objeto=convite.grupo.nome,
            dados_anteriores={"convite_id": convite.id},
        )
        messages.success(request, f"Voce agora faz parte do grupo '{convite.grupo.nome}'!")
    else:
        registrar_log(
            usuario=request.user,
            acao="RECUSAR_CONVITE_GRUPO",
            id_objeto_alvo=convite.grupo.id,
            nome_objeto=convite.grupo.nome,
            dados_anteriores={"convite_id": convite.id},
        )
        messages.info(request, f"Convite para o grupo '{convite.grupo.nome}' recusado.")

    convite.delete()
    return redirect("meus_convites")


@usuario
def meus_grupos_administrados(request):
    grupos = Grupo.objects.filter(membros=request.user).distinct().order_by("nome")
    return render(request, "meus_grupos.html", {"grupos": grupos})


@usuario
@require_POST
def sair_do_grupo(request, grupo_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo desejado.")
        return redirect("meus_grupos_administrados")

    if request.user not in grupo.membros.all():
        messages.error(request, "Voce nao faz parte deste grupo.")
        return redirect("meus_grupos_administrados")

    if request.user in grupo.administradores.all() and grupo.administradores.count() <= 1:
        if grupo.membros.count() > 1:
            messages.error(
                request,
                "Voce e o unico administrador deste grupo. Promova outro membro a administrador antes de sair.",
            )
            return redirect("gerenciar_grupo", grupo_id=grupo.id)

        grupo_id_excluido = grupo.id
        nome_grupo = grupo.nome
        registrar_log(
            usuario=request.user,
            acao="SAIR_GRUPO",
            id_objeto_alvo=grupo_id_excluido,
            nome_objeto=nome_grupo,
        )
        registrar_log(
            usuario=request.user,
            acao="EXCLUIR_GRUPO",
            id_objeto_alvo=grupo_id_excluido,
            nome_objeto=nome_grupo,
        )
        grupo.delete()
        messages.success(request, f"Voce saiu e o grupo '{nome_grupo}' foi desfeito por estar vazio.")
        return redirect("meus_grupos_administrados")

    grupo.membros.remove(request.user)
    if request.user in grupo.administradores.all():
        grupo.administradores.remove(request.user)
    registrar_log(
        usuario=request.user,
        acao="SAIR_GRUPO",
        id_objeto_alvo=grupo.id,
        nome_objeto=grupo.nome,
    )

    messages.success(request, f"Voce saiu do grupo '{grupo.nome}' com sucesso.")
    return redirect("meus_grupos_administrados")


@admin_grupo
@require_POST
def remover_membro(request, grupo_id, usuario_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
        usuario_alvo = Usuario.objects.get(id=usuario_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo ou usuario desejado.")
        return redirect("meus_grupos_administrados")

    if not usuario_administra_grupo(request, grupo):
        messages.error(request, "Voce nao tem permissao para remover membros deste grupo.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    if usuario_alvo == request.user:
        messages.error(request, "Voce nao pode se remover do grupo por este botao.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    grupo.membros.remove(usuario_alvo)
    if usuario_alvo in grupo.administradores.all():
        grupo.administradores.remove(usuario_alvo)
    registrar_log(
        usuario=request.user,
        acao="REMOVER_MEMBRO",
        id_objeto_alvo=grupo.id,
        nome_objeto=grupo.nome,
        dados_anteriores={"usuario_id": usuario_alvo.id},
    )

    messages.success(request, f"Usuario '{usuario_alvo.username}' foi removido do grupo.")
    return redirect("gerenciar_grupo", grupo_id=grupo.id)


@admin_grupo
@require_POST
def promover_administrador(request, grupo_id, usuario_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
        usuario_alvo = Usuario.objects.get(id=usuario_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo ou usuario desejado.")
        return redirect("meus_grupos_administrados")

    if not usuario_administra_grupo(request, grupo):
        messages.error(request, "Voce nao tem permissao para promover membros deste grupo.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    if usuario_alvo not in grupo.membros.all():
        messages.error(request, "O usuario precisa ser membro do grupo antes de se tornar administrador.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    if usuario_alvo in grupo.administradores.all():
        messages.warning(request, f"'{usuario_alvo.username}' ja e um administrador deste grupo.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    grupo.administradores.add(usuario_alvo)
    registrar_log(
        usuario=request.user,
        acao="PROMOVER_ADMIN_GRUPO",
        id_objeto_alvo=grupo.id,
        nome_objeto=grupo.nome,
        dados_anteriores={"usuario_id": usuario_alvo.id},
    )

    messages.success(request, f"Usuario '{usuario_alvo.username}' agora tambem e administrador do grupo!")
    return redirect("gerenciar_grupo", grupo_id=grupo.id)


@admin_grupo
@require_POST
def revogar_administrador(request, grupo_id, usuario_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
        usuario_alvo = Usuario.objects.get(id=usuario_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo ou usuario desejado.")
        return redirect("meus_grupos_administrados")

    if not usuario_administra_grupo(request, grupo):
        messages.error(request, "Voce nao tem permissao para alterar privilegios neste grupo.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    if usuario_alvo not in grupo.administradores.all():
        messages.warning(request, f"'{usuario_alvo.username}' nao e um administrador deste grupo.")
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    # Um grupo nunca pode ficar sem administrador responsavel.
    if grupo.administradores.count() <= 1:
        messages.error(
            request,
            "O grupo deve ter pelo menos um administrador. Promova outro membro antes de revogar este acesso.",
        )
        return redirect("gerenciar_grupo", grupo_id=grupo.id)

    grupo.administradores.remove(usuario_alvo)
    registrar_log(
        usuario=request.user,
        acao="REVOGAR_ADMIN_GRUPO",
        id_objeto_alvo=grupo.id,
        nome_objeto=grupo.nome,
        dados_anteriores={"usuario_id": usuario_alvo.id},
    )

    messages.success(request, f"Os privilegios de administrador de '{usuario_alvo.username}' foram revogados.")

    if usuario_alvo == request.user:
        return redirect("meus_grupos_administrados")

    return redirect("gerenciar_grupo", grupo_id=grupo.id)


@admin_grupo
@require_POST
def excluir_grupo(request, grupo_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo desejado.")
        return redirect("meus_grupos_administrados")

    if not usuario_administra_grupo(request, grupo):
        messages.error(request, "Voce nao tem permissao para excluir este grupo.")
        return redirect("meus_grupos_administrados")

    nome_grupo = grupo.nome
    grupo_id_excluido = grupo.id
    grupo.membros.clear()
    grupo.administradores.clear()

    grupo.delete()
    registrar_log(
        usuario=request.user,
        acao="EXCLUIR_GRUPO",
        id_objeto_alvo=grupo_id_excluido,
        nome_objeto=nome_grupo,
    )

    messages.success(request, f"O grupo '{nome_grupo}' foi excluido permanentemente.")
    return redirect("meus_grupos_administrados")
