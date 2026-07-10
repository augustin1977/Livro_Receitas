"""Views de login, logout e manutencao de senha."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_django
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

from autentica import usuario
from logs.utils import registrar_log

from .models import Usuario


def login(request):
    """Exibe a tela de login e repassa o status usado pelas mensagens da pagina."""
    status = str(request.GET.get("status"))
    return render(request, "login.html", {"status": status})


@usuario
def alterar_senha(request):
    """Permite ao usuario autenticado trocar a senha informando a senha atual."""
    if request.method == "POST":
        senha_atual = request.POST.get("senha_atual")
        nova_senha = request.POST.get("nova_senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        if not request.user.check_password(senha_atual):
            messages.error(request, "Senha atual incorreta.")
            return redirect("alterar_senha")

        if nova_senha != confirmar_senha:
            messages.error(request, "As novas senhas nao conferem.")
            return redirect("alterar_senha")

        if len(nova_senha) < 6:
            messages.error(request, "A nova senha deve ter pelo menos 6 caracteres.")
            return redirect("alterar_senha")

        request.user.set_password(nova_senha)
        request.user.deve_trocar_senha = False
        request.user.save()
        registrar_log(
            usuario=request.user,
            acao="ALTERAR_SENHA",
            id_objeto_alvo=request.user.id,
            nome_objeto=request.user.username,
        )

        login_django(request, request.user)

        messages.success(request, "Senha alterada com sucesso.")
        return redirect("home")

    return render(request, "alterar_senha.html")


def esqueci_senha(request):
    """Gera uma senha provisoria por e-mail e marca troca obrigatoria no proximo login."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, "Nao existe usuario cadastrado com este e-mail.")
            return redirect("esqueci_senha")
        try:
            senha_provisoria = get_random_string(10)
            send_mail(
                "Senha provisoria - Livro de Receitas",
                (
                    f"Sua senha provisoria e: {senha_provisoria}\n\n"
                    "Ao entrar no sistema, voce sera obrigado a criar uma nova senha."
                ),
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )
            usuario.set_password(senha_provisoria)
            usuario.deve_trocar_senha = True
            usuario.save()
            registrar_log(
                usuario=usuario,
                acao="ALTERAR_SENHA",
                id_objeto_alvo=usuario.id,
                nome_objeto=usuario.username,
            )

            messages.success(request, "Uma senha provisoria foi enviada para seu e-mail.")
            return redirect("login")
        except Exception:
            messages.error(
                request,
                "Erro na recuperacao de senha, por favor tente novamente ou entre em contato com o suporte",
            )
    return render(request, "esqueci_senha.html")


@usuario
def trocar_senha_obrigatoria(request):
    """Forca a criacao de nova senha quando o usuario esta com senha provisoria."""
    if not request.user.deve_trocar_senha:
        return redirect("home")

    if request.method == "POST":
        nova_senha = request.POST.get("nova_senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        if nova_senha != confirmar_senha:
            messages.error(request, "As senhas nao conferem.")
            return redirect("trocar_senha_obrigatoria")

        if len(nova_senha) < 6:
            messages.error(request, "A nova senha deve ter pelo menos 6 caracteres.")
            return redirect("trocar_senha_obrigatoria")

        request.user.set_password(nova_senha)
        request.user.deve_trocar_senha = False
        request.user.save()
        registrar_log(
            usuario=request.user,
            acao="ALTERAR_SENHA",
            id_objeto_alvo=request.user.id,
            nome_objeto=request.user.username,
        )

        login_django(request, request.user)

        messages.success(request, "Senha alterada com sucesso.")
        return redirect("home")

    return render(request, "trocar_senha_obrigatoria.html")


def validar_login(request):
    """Autentica credenciais e direciona usuarios com senha provisoria para troca."""
    if request.method != "POST":
        return redirect("login")

    nome = request.POST.get("username", "").strip()
    senha = request.POST.get("senha", "")

    try:
        usuario_objeto = Usuario.objects.get(username=nome)
    except Usuario.DoesNotExist:
        return redirect("/auth/login/?status=1")

    usuario_autenticado = authenticate(
        request,
        username=usuario_objeto.username,
        password=senha,
    )

    if usuario_autenticado is None:
        messages.error(request, "Usuario ou senha invalidos.")
        return redirect("login")

    login_django(request, usuario_autenticado)

    if usuario_autenticado.deve_trocar_senha:
        return redirect("trocar_senha_obrigatoria")

    return redirect("/receita/home/")


@usuario
@require_POST
def sair(request):
    """Logout tambem exige POST para evitar encerramento de sessao por link externo."""
    request.session.flush()
    return redirect("/auth/login")
