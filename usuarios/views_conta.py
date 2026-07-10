"""Views de cadastro, perfil e administracao de contas."""

import re

from django.contrib import messages
from django.contrib.auth import login as login_django
from django.contrib.auth import logout
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from autentica import admin_geral, usuario
from logs.utils import registrar_log
from receita.models import Ingrediente, Receita

from .models import Grupo, Tipo, Usuario


@usuario
def excluir_conta(request):
    if request.method == "POST":
        senha = request.POST.get("senha")
        confirmar = request.POST.get("confirmar")

        if confirmar != "EXCLUIR":
            messages.error(request, "Digite EXCLUIR para confirmar.")
            return redirect("excluir_conta")

        if not request.user.check_password(senha):
            messages.error(request, "Senha incorreta.")
            return redirect("excluir_conta")

        usuario_atual = request.user
        registrar_log(
            usuario=usuario_atual,
            acao="EXCLUIR_USUARIO",
            id_objeto_alvo=usuario_atual.id,
            nome_objeto=usuario_atual.username,
        )

        receitas = Receita.objects.filter(usuario=usuario_atual)
        Ingrediente.objects.filter(receita__in=receitas).delete()
        receitas.delete()

        usuario_atual.grupos.clear()
        usuario_atual.grupos_administrados.clear()
        usuario_atual.convites_recebidos.all().delete()

        logout(request)
        usuario_atual.delete()

        messages.success(request, "Sua conta foi excluida com sucesso.")
        return redirect("login")

    return render(request, "excluir_conta.html")


@admin_geral
def listar_usuarios(request):
    usuarios = Usuario.objects.all().order_by("username")
    return render(request, "listar_usuarios.html", {"usuarios": usuarios})


@admin_geral
def excluir_usuario_admin(request, usuario_id):
    usuario_alvo = get_object_or_404(Usuario, id=usuario_id)

    if usuario_alvo == request.user:
        messages.error(request, "Voce nao pode excluir sua propria conta por esta tela.")
        return redirect("listar_usuarios")

    if request.method == "POST":
        receitas = Receita.objects.filter(usuario=usuario_alvo)
        Ingrediente.objects.filter(receita__in=receitas).delete()
        receitas.delete()

        usuario_alvo.grupos.clear()
        usuario_alvo.grupos_administrados.clear()
        usuario_alvo.convites_recebidos.all().delete()

        nome = usuario_alvo.username
        registrar_log(
            usuario=request.user,
            acao="EXCLUIR_USUARIO",
            id_objeto_alvo=usuario_alvo.id,
            nome_objeto=nome,
        )
        usuario_alvo.delete()

        messages.success(request, f"Usuario '{nome}' excluido com sucesso.")
        return redirect("listar_usuarios")

    return render(request, "confirmar_excluir_usuario.html", {
        "usuario_alvo": usuario_alvo,
    })


def cadastrar(request):
    status = str(request.GET.get("status"))
    return render(request, "cadastro.html", {"status": status})


@usuario
def editar(request):
    usuario_logado = request.user

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        nome_completo = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        senha = request.POST.get("senha", "").strip()

        if not username or not nome_completo or not email:
            messages.error(
                request,
                "Nome de usuario, nome completo e e-mail sao obrigatorios.",
            )
            return redirect("editar")

        if Usuario.objects.exclude(id=usuario_logado.id).filter(username=username).exists():
            messages.error(request, "Este nome de usuario ja esta em uso.")
            return redirect("editar")

        if Usuario.objects.exclude(id=usuario_logado.id).filter(email=email).exists():
            messages.error(request, "Este e-mail ja esta em uso.")
            return redirect("editar")

        dados_anteriores = {
            "username": usuario_logado.username,
            "first_name": usuario_logado.first_name,
            "last_name": usuario_logado.last_name,
            "email": usuario_logado.email,
        }
        partes_nome = nome_completo.split()
        usuario_logado.username = username
        usuario_logado.first_name = partes_nome[0]
        usuario_logado.last_name = " ".join(partes_nome[1:])
        usuario_logado.email = email

        if senha:
            usuario_logado.set_password(senha)

        usuario_logado.save()
        registrar_log(
            usuario=usuario_logado,
            acao="EDITAR_USUARIO",
            id_objeto_alvo=usuario_logado.id,
            nome_objeto=usuario_logado.username,
            dados_anteriores=dados_anteriores,
        )

        if senha:
            login_django(request, usuario_logado)

        messages.success(request, "Cadastro atualizado com sucesso.")
        return redirect("home")

    nome_completo = f"{usuario_logado.first_name} {usuario_logado.last_name}".strip()

    return render(request, "editar.html", {
        "usuario_editando": usuario_logado,
        "nome_completo": nome_completo,
    })


def valida_cadastro(request):
    if request.method != "POST":
        return redirect("cadastrar")

    username = request.POST.get("username", "").strip()
    nome_completo_cru = request.POST.get("nome", "").strip()
    nome = nome_completo_cru.split()
    email = request.POST.get("email", "").strip()
    senha = request.POST.get("senha", "")

    contexto_retorno = {
        "username_digitado": username,
        "nome_digitado": nome_completo_cru,
        "email_digitado": email,
    }

    if not username or not nome or not email or not senha:
        messages.error(request, "Todos os campos sao obrigatorios. Verifique o formulario.")
        return render(request, "cadastro.html", contexto_retorno)

    first_name = str(nome[0])
    last_name = " ".join(nome[1:])

    regex_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    retorno = False
    if not re.match(regex_email, email):
        messages.error(request, "E-mail invalido. Por favor, verifique a grafia.")
        retorno = True

    regex_senha = r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%<^&*?()])[a-zA-Z0-9!@#$%<^&*?()]{6,}"
    if not re.match(regex_senha, senha):
        messages.error(
            request,
            "Senha muito curta. Ela deve ter no minimo 6 caracteres e conter letras maiusculas, minusculas, numeros e simbolos.",
        )
        retorno = True

    if Usuario.objects.filter(username=username).exists():
        messages.error(request, "Este nome de usuario (nickname) ja esta cadastrado.")
        retorno = True

    if Usuario.objects.filter(email=email).exists():
        messages.error(request, "Este e-mail ja esta cadastrado. Esqueceu a senha?")
        retorno = True

    if retorno:
        return render(request, "cadastro.html", contexto_retorno)

    try:
        tipo_padrao = Tipo.objects.get(tipo="user")

        novo_usuario = Usuario.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=senha,
            tipo=tipo_padrao,
        )
        registrar_log(
            usuario=novo_usuario,
            acao="CADASTRAR_USUARIO",
            id_objeto_alvo=novo_usuario.id,
            nome_objeto=novo_usuario.username,
        )

        try:
            grupo_padrao = Grupo.objects.get(nome="Sem_Familia")
            grupo_padrao.membros.add(novo_usuario)
        except Grupo.DoesNotExist:
            pass

        messages.success(request, f"Usuario '{username}' cadastrado com sucesso! Faca seu login.")
        return redirect("login")

    except IntegrityError as integrity:
        messages.error(
            request,
            f"Erro de integridade ao salvar o usuario. Tente dados diferentes./n{integrity}",
        )
        return render(request, "cadastro.html", contexto_retorno)
    except Exception as erro:
        messages.error(request, f"Erro Geral no cadastro de Usuarios: {str(erro)}")
        return render(request, "cadastro.html", contexto_retorno)
