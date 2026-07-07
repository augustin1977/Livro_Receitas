from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import *
from receita.models import *
from django.shortcuts import redirect 
from hashlib import sha256
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_django, logout
from autentica import *
from django.db import IntegrityError
import re
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
def login(request):
    # cria a view do login do usuário
    status=str(request.GET.get('status'))
    return render(request, "login.html", {'status':status})
@usuario
def alterar_senha(request):
    if request.method == "POST":
        senha_atual = request.POST.get("senha_atual")
        nova_senha = request.POST.get("nova_senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        if not request.user.check_password(senha_atual):
            messages.error(request, "Senha atual incorreta.")
            return redirect("alterar_senha")

        if nova_senha != confirmar_senha:
            messages.error(request, "As novas senhas não conferem.")
            return redirect("alterar_senha")

        if len(nova_senha) < 6:
            messages.error(request, "A nova senha deve ter pelo menos 6 caracteres.")
            return redirect("alterar_senha")

        request.user.set_password(nova_senha)
        request.user.deve_trocar_senha = False
        request.user.save()

        login_django(request, request.user)

        messages.success(request, "Senha alterada com sucesso.")
        return redirect("home")

    return render(request, "alterar_senha.html")
def esqueci_senha(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, "Não existe usuário cadastrado com este e-mail.")
            return redirect("esqueci_senha")

        senha_provisoria = get_random_string(10)

        usuario.set_password(senha_provisoria)
        usuario.deve_trocar_senha = True
        usuario.save()

        send_mail(
            "Senha provisória - Livro de Receitas",
            f"Sua senha provisória é: {senha_provisoria}\n\nAo entrar no sistema, você será obrigado a criar uma nova senha.",
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            fail_silently=False,
        )

        messages.success(request, "Uma senha provisória foi enviada para seu e-mail.")
        return redirect("login")

    return render(request, "esqueci_senha.html")

@usuario
def trocar_senha_obrigatoria(request):
    if not request.user.deve_trocar_senha:
        return redirect("home")

    if request.method == "POST":
        nova_senha = request.POST.get("nova_senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        if nova_senha != confirmar_senha:
            messages.error(request, "As senhas não conferem.")
            return redirect("trocar_senha_obrigatoria")

        if len(nova_senha) < 6:
            messages.error(request, "A nova senha deve ter pelo menos 6 caracteres.")
            return redirect("trocar_senha_obrigatoria")

        request.user.set_password(nova_senha)
        request.user.deve_trocar_senha = False
        request.user.save()

        login_django(request, request.user)

        messages.success(request, "Senha alterada com sucesso.")
        return redirect("home")

    return render(request, "trocar_senha_obrigatoria.html")

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

        usuario = request.user

        receitas = Receita.objects.filter(usuario=usuario)
        Ingrediente.objects.filter(receita__in=receitas).delete()
        receitas.delete()

        usuario.grupos.clear()
        usuario.grupos_administrados.clear()
        usuario.convites_recebidos.all().delete()

        logout(request)
        usuario.delete()

        messages.success(request, "Sua conta foi excluída com sucesso.")
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
        messages.error(request, "Você não pode excluir sua própria conta por esta tela.")
        return redirect("listar_usuarios")

    if request.method == "POST":
        receitas = Receita.objects.filter(usuario=usuario_alvo)
        Ingrediente.objects.filter(receita__in=receitas).delete()
        receitas.delete()

        usuario_alvo.grupos.clear()
        usuario_alvo.grupos_administrados.clear()
        usuario_alvo.convites_recebidos.all().delete()

        nome = usuario_alvo.username
        usuario_alvo.delete()

        messages.success(request, f"Usuário '{nome}' excluído com sucesso.")
        return redirect("listar_usuarios")

    return render(request, "confirmar_excluir_usuario.html", {
        "usuario_alvo": usuario_alvo
    })
def cadastrar(request):
    # cria a view do cadastro de usuaário
    status=str(request.GET.get('status'))
    return render(request, "cadastro.html", {'status':status})
@usuario
def editar(request):
    usuario_logado = request.user

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        nome_completo = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        senha = request.POST.get("senha", "").strip()

        if not username or not nome_completo or not email:
            messages.error(request, "Nome de usuário, nome completo e e-mail são obrigatórios.")
            return redirect("editar")

        if Usuario.objects.exclude(id=usuario_logado.id).filter(username=username).exists():
            messages.error(request, "Este nome de usuário já está em uso.")
            return redirect("editar")

        if Usuario.objects.exclude(id=usuario_logado.id).filter(email=email).exists():
            messages.error(request, "Este e-mail já está em uso.")
            return redirect("editar")

        partes_nome = nome_completo.split()
        usuario_logado.username = username
        usuario_logado.first_name = partes_nome[0]
        usuario_logado.last_name = " ".join(partes_nome[1:])
        usuario_logado.email = email

        if senha:
            usuario_logado.set_password(senha)

        usuario_logado.save()

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
        return redirect('cadastrar')

    # 1. Captura os dados do novo formulário
    username = request.POST.get('username', '').strip()
    nome_completo_cru = request.POST.get('nome', '').strip() # Guardamos o texto original digitado
    nome = nome_completo_cru.split()
    email = request.POST.get('email', '').strip()
    senha = request.POST.get('senha', '')
    
    # Criamos um dicionário com os dados atuais para devolver ao HTML se der erro
    contexto_retorno = {
        'username_digitado': username,
        'nome_digitado': nome_completo_cru,
        'email_digitado': email
    }

    # 2. Validação de campos vazios
    if not username or not nome or not email or not senha:
        messages.error(request, "Todos os campos são obrigatórios. Verifique o formulário.")
        return render(request, 'cadastro.html', contexto_retorno)

    first_name = str(nome[0])
    last_name = " ".join(nome[1:])

    # 3. Validação de formato de e-mail
    regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    retorno= False
    if not re.match(regex_email, email):
        messages.error(request, "E-mail inválido. Por favor, verifique a grafia.")
        retorno=True

    # 4. Validação de força da senha
    regex_senha = r"^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%<^&*?()])[a-zA-Z0-9!@#$%<^&*?()]{6,}"
    if not re.match(regex_senha, senha):
        messages.error(request, "Senha muito curta. Ela deve ter no mínimo 6 caracteres e conter letras maiúsculas, minúsculas, números e símbolos.")
        retorno=True

    # 5. Verificação de duplicidade no banco
    if Usuario.objects.filter(username=username).exists():
        messages.error(request, "Este nome de usuário (nickname) já está cadastrado.")
        retorno=True

    if Usuario.objects.filter(email=email).exists():
        messages.error(request, "Este e-mail já está cadastrado. Esqueceu a senha?")
        retorno=True

    if retorno:
        return render(request, 'cadastro.html', contexto_retorno)
    # 6. Processo de gravação segura
    try:
        tipo_padrao = Tipo.objects.get(tipo="user")
        
        novo_usuario = Usuario.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=senha,
            tipo=tipo_padrao
        )

        try:
            grupo_padrao = Grupo.objects.get(nome="Sem_Familia")
            grupo_padrao.membros.add(novo_usuario)
        except Grupo.DoesNotExist:
            pass

        messages.success(request, f"Usuário '{username}' cadastrado com sucesso! Faça seu login.")
        return redirect('login')

    except IntegrityError as integrity:
        messages.error(request, f"Erro de integridade ao salvar o usuário. Tente dados diferentes./n{integrity}")
        return render(request, 'cadastro.html', contexto_retorno)
    except Exception as e:
        messages.error(request, f"Erro Geral no cadastro de Usuários: {str(e)}")
        return render(request, 'cadastro.html', contexto_retorno)

def validar_login(request):
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
        password=senha
    )

    if usuario_autenticado is None:
        messages.error(request, "Usuário ou senha inválidos.")
        return redirect("login")

    login_django(request, usuario_autenticado)

    if usuario_autenticado.deve_trocar_senha:
        return redirect("trocar_senha_obrigatoria")

    return redirect("/receita/home/")

@usuario    
def sair(request):
    request.session.flush() # sair do usuário
    return redirect('/auth/login')

@usuario
def cadastrar_grupo(request):
    if request.method == "POST":
        nome_grupo = request.POST.get('nome', '').strip()
        
        if not nome_grupo:
            messages.error(request, "O nome do grupo não pode ficar em branco.")
            return redirect('cadastrar_grupo')
            
        if Grupo.objects.filter(nome=nome_grupo).exists():
            messages.error(request, "Já existe um grupo com este nome.")
            return redirect('cadastrar_grupo')
            
        # Cria o grupo
        novo_grupo = Grupo.objects.create(nome=nome_grupo)
        # Adiciona o criador como membro e como administrador
        novo_grupo.membros.add(request.user)
        novo_grupo.administradores.add(request.user)
        
        messages.success(request, f"Grupo '{nome_grupo}' criado com sucesso! Agora você pode adicionar membros.")
        return redirect('gerenciar_grupo', grupo_id=novo_grupo.id)
        
    return render(request, "cadastrar_grupo.html")

@usuario
def gerenciar_grupo(request, grupo_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except:
        messages.error(request, "Erro ao acessar o grupo desejado.")
        return redirect('meus_grupos_administrados')
    
    # Trava de segurança: apenas membros ou administradores gerais podem ver o grupo
    if request.user not in grupo.membros.all(): # and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar este grupo.")
        return redirect('meus_grupos_administrados')
        
    return render(request, "gerenciar_grupo.html", {'grupo': grupo})

@usuario
def adicionar_membro(request, grupo_id):
    if request.method != "POST":
        return redirect('meus_grupos_administrados')
        
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Exception:
        messages.error(request, "Grupo não encontrado.")
        return redirect('meus_grupos_administrados')
        
    # Trava de segurança: apenas administradores do grupo ou admin geral
    if request.user not in grupo.administradores.all() and not request.user.is_staff:
        messages.error(request, "Permissão negada.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)
        
    busca = request.POST.get('busca', '').strip()
    
    # Busca o usuário alvo
    try:
        usuario_alvo = Usuario.objects.get(username=busca)
    except Usuario.DoesNotExist:
        try:
            usuario_alvo = Usuario.objects.get(email=busca)
        except Usuario.DoesNotExist:
            messages.error(request, f"Usuário '{busca}' não encontrado.")
            return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # Verifica se já é membro
    if usuario_alvo in grupo.membros.all():
        messages.warning(request, f"'{usuario_alvo.username}' já faz parte deste grupo.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)
        
    # Verifica se já existe um convite pendente para ele neste mesmo grupo
    if ConviteGrupo.objects.filter(grupo=grupo, usuario_convidado=usuario_alvo).exists():
        messages.warning(request, f"Já existe um convite pendente para '{usuario_alvo.username}'.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)
        
    # Em vez de adicionar direto, cria o convite pendente
    ConviteGrupo.objects.create(grupo=grupo, usuario_convidado=usuario_alvo)
    messages.success(request, f"Convite enviado para '{usuario_alvo.username}'. Aguardando aprovação dele.")
    return redirect('gerenciar_grupo', grupo_id=grupo.id)

@usuario
def meus_convites(request):
    # Lista todos os convites direcionados ao usuário logado
    convites = ConviteGrupo.objects.filter(usuario_convidado=request.user).order_by('-data_envio')
    return render(request, "meus_convites.html", {'convites': convites})
@usuario
def responder_convite(request, convite_id, acao):
    try:
        convite = ConviteGrupo.objects.get(id=convite_id, usuario_convidado=request.user)
    except Exception:
        messages.error(request, "Convite não encontrado ou já processado.")
        return redirect('meus_convites')

    if acao == 'aceitar':
        convite.grupo.membros.add(request.user)
        messages.success(request, f"Você agora faz parte do grupo '{convite.grupo.nome}'!")
    else:
        messages.info(request, f"Convite para o grupo '{convite.grupo.nome}' recusado.")
        
    # Apaga o convite do banco após processar a decisão
    convite.delete()
    return redirect('meus_convites')

@usuario
def meus_grupos_administrados(request):
    # Traz todos os grupos em que o usuário está na lista de membros (seja admin ou comum)
    grupos = Grupo.objects.filter(membros=request.user).distinct().order_by('nome')
    return render(request, "meus_grupos.html", {'grupos': grupos})

@usuario
def sair_do_grupo(request, grupo_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo desejado.")
        return redirect('meus_grupos_administrados')

    # Se o usuário não estiver no grupo, não há o que fazer
    if request.user not in grupo.membros.all():
        messages.error(request, "Você não faz parte deste grupo.")
        return redirect('meus_grupos_administrados')

    # REGRA DE SEGURANÇA: Se ele for administrador, precisamos checar se o grupo não vai ficar órfão
    if request.user in grupo.administradores.all() and grupo.administradores.count() <= 1:
        # Se houver mais membros, ele precisa promover alguém antes de sair
        if grupo.membros.count() > 1:
            messages.error(request, "Você é o único administrador deste grupo. Promova outro membro a administrador antes de sair.")
            return redirect('gerenciar_grupo', grupo_id=grupo.id)
        # Se ele for o único membro do grupo inteiro, o grupo será deletado automaticamente ao sair
        else:
            grupo.delete()
            messages.success(request, f"Você saiu e o grupo '{grupo.nome}' foi desfeito por estar vazio.")
            return redirect('meus_grupos_administrados')

    # Fluxo normal: remove dos membros e dos administradores (caso fosse um)
    grupo.membros.remove(request.user)
    if request.user in grupo.administradores.all():
        grupo.administradores.remove(request.user)

    messages.success(request, f"Você saiu do grupo '{grupo.nome}' com sucesso.")
    return redirect('meus_grupos_administrados')
@admin_grupo
def remover_membro(request, grupo_id, usuario_id):
    # Tratamento de erro customizado sem telas de erro técnicas do Django
    try:
        grupo = Grupo.objects.get(id=grupo_id)
        usuario_alvo = Usuario.objects.get(id=usuario_id)
    except Exception as e:
        messages.error(request, "Erro ao acessar o grupo ou usuário desejado.")
        return redirect('meus_grupos_administrados')

    # Trava de segurança: usa o campo correto 'administradores'
    if request.user not in grupo.administradores.all() and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para remover membros deste grupo.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # Impede que o administrador se remova por acidente
    if usuario_alvo == request.user:
        messages.error(request, "Você não pode se remover do grupo por este botão.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # Remove o usuário da lista de membros e de administradores
    grupo.membros.remove(usuario_alvo)
    if usuario_alvo in grupo.administradores.all():
        grupo.administradores.remove(usuario_alvo)

    messages.success(request, f"Usuário '{usuario_alvo.username}' foi removido do grupo.")
    return redirect('gerenciar_grupo', grupo_id=grupo.id)

@admin_grupo
def promover_administrador(request, grupo_id, usuario_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
        usuario_alvo = Usuario.objects.get(id=usuario_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo ou usuário desejado.")
        return redirect('meus_grupos_administrados')

    # Trava de segurança: apenas administradores do grupo ou admin geral podem promover
    if request.user not in grupo.administradores.all() and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para promover membros deste grupo.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # O usuário alvo precisa ser membro do grupo para virar admin
    if usuario_alvo not in grupo.membros.all():
        messages.error(request, "O usuário precisa ser membro do grupo antes de se tornar administrador.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # Verifica se ele já é admin
    if usuario_alvo in grupo.administradores.all():
        messages.warning(request, f"'{usuario_alvo.username}' já é um administrador deste grupo.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # Adiciona à lista de administradores
    grupo.administradores.add(usuario_alvo)

    messages.success(request, f"Usuário '{usuario_alvo.username}' agora também é administrador do grupo!")
    return redirect('gerenciar_grupo', grupo_id=grupo.id)
@admin_grupo
def revogar_administrador(request, grupo_id, usuario_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
        usuario_alvo = Usuario.objects.get(id=usuario_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo ou usuário desejado.")
        return redirect('meus_grupos_administrados')

    # Trava de segurança: apenas administradores do grupo ou admin geral podem revogar
    if request.user not in grupo.administradores.all():
        messages.error(request, "Você não tem permissão para alterar privilégios neste grupo.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # Verifica se o usuário alvo realmente é um administrador do grupo
    if usuario_alvo not in grupo.administradores.all():
        messages.warning(request, f"'{usuario_alvo.username}' não é um administrador deste grupo.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # REGRA CRÍTICA: Impede que o grupo fique sem nenhum administrador
    if grupo.administradores.count() <= 1:
        messages.error(request, "O grupo deve ter pelo menos um administrador. Promova outro membro antes de revogar este acesso.")
        return redirect('gerenciar_grupo', grupo_id=grupo.id)

    # Remove da lista de administradores (mas ele continua sendo membro comum do grupo)
    grupo.administradores.remove(usuario_alvo)

    messages.success(request, f"Os privilégios de administrador de '{usuario_alvo.username}' foram revogados.")
    
    # Se o usuário logado revogou a si mesmo, ele perde o acesso de gestão e deve ser jogado para a lista de grupos dele
    if usuario_alvo == request.user:
        return redirect('meus_grupos_administrados')
        
    return redirect('gerenciar_grupo', grupo_id=grupo.id)
@admin_grupo
def excluir_grupo(request, grupo_id):
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Exception:
        messages.error(request, "Erro ao acessar o grupo desejado.")
        return redirect('meus_grupos_administrados')

    # Trava de segurança: apenas quem está na lista de administradores do grupo ou admin geral pode deletar
    if request.user not in grupo.administradores.all():
        messages.error(request, "Você não tem permissão para excluir este grupo.")
        return redirect('meus_grupos_administrados')

    nome_grupo = grupo.nome
        # Remove todos os vínculos de membros e administradores antes de apagar (boa prática do Django)
    grupo.membros.clear()
    grupo.administradores.clear()
    
    # Deleta o grupo definitivamente
    grupo.delete()

    messages.success(request, f"O grupo '{nome_grupo}' foi excluído permanentemente.")
    return redirect('meus_grupos_administrados')