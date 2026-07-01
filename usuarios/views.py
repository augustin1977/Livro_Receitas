from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Usuario,Tipo,Grupo
from django.shortcuts import redirect 
from hashlib import sha256
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_django
from autentica import *
from django.db import IntegrityError
import re
def login(request):
    # cria a view do login do usuário
    status=str(request.GET.get('status'))
    return render(request, "login.html", {'status':status})

def cadastrar(request):
    # cria a view do cadastro de usuaário
    status=str(request.GET.get('status'))
    return render(request, "cadastro.html", {'status':status})
@usuario_obrigatorio
def editar(request):
    # Cria a view que edita o cadastro do usuário, ainda não implementado
    return render(request, "editar.html")

def valida_cadastro(request):
    if request.method != "POST":
        return redirect('cadastrar_usuario')

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
    if request.method == "POST":
        nome = request.POST.get('username')
        senha = request.POST.get('senha')
        
        # 1. Como o login padrão do Django busca por 'username', precisamos
        # encontrar o username correspondente ao e-mail digitado.
        try:
            usuario_objeto = Usuario.objects.get(username=nome)
            username = usuario_objeto.username
        except Usuario.DoesNotExist:
            # Se o e-mail não existir, redireciona informando erro
            return redirect('/auth/login/?status=1')

        # 2. O authenticate valida se o username e a senha batem
        usuario_autenticado = authenticate(request, username=username, password=senha)
        
        if usuario_autenticado is not None:
            # 3. Loga o usuário criando a sessão segura nativa do Django
            login_django(request, usuario_autenticado)
            return redirect('/receita/home/')
        else:
            # Senha incorreta
            return redirect('/auth/login/?status=1')
            
    # Caso tentem acessar a URL via GET diretamente
    return redirect('/auth/login/')
    
def sair(request):
    request.session.flush() # sair do usuário
    return redirect('/auth/login')

@usuario_obrigatorio
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

@usuario_obrigatorio
def gerenciar_grupo(request, grupo_id):
    try:
        grupo = Grupo.objects.get( id=grupo_id)
        print(grupo)
    except:
        messages.error(request, "Erro ao acessar o grupo desejado.")
        return redirect('/receita/home/')
    
    # Trava de segurança: apenas membros ou administradores gerais podem ver o grupo
    if request.user not in grupo.membros.all() and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar este grupo.")
        return redirect('/receita/home/')
        
    return render(request, "gerenciar_grupo.html", {'grupo': grupo})

@usuario_obrigatorio
def adicionar_membro(request, grupo_id):
    if request.method == "POST":
        try:
            grupo = Grupo.objects.get(id=grupo_id)
        except Exception as e:
            messages.error(request, f"Erro ao acessar o grupo desejado.")
            return redirect('/receita/home/')
    
        
        # Trava de segurança: apenas administradores do grupo ou admin geral podem pôr pessoas
        if request.user not in grupo.administradores.all() and not request.user.is_staff:
            messages.error(request, "Apenas administradores do grupo podem adicionar membros.")
            return redirect('gerenciar_grupo', grupo_id=grupo.id)
            
        busca = request.POST.get('busca', '').strip()
        
        # Procura por nickname (username) ou e-mail
        try:
            novo_membro = Usuario.objects.get(username=busca)
        except Usuario.DoesNotExist:
            try:
                novo_membro = Usuario.objects.get(email=busca)
            except Usuario.DoesNotExist:
                messages.error(request, f"Nenhum usuário encontrado com o login ou e-mail '{busca}'.")
                return redirect('gerenciar_grupo', grupo_id=grupo.id)
                
        if novo_membro in grupo.membros.all():
            messages.warning(request, f"O usuário '{novo_membro.username}' os dados já faz parte deste grupo.")
        else:
            grupo.membros.add(novo_membro)
            messages.success(request, f"Usuário '{novo_membro.username}' adicionado ao grupo com sucesso.")
            
    return redirect('gerenciar_grupo', grupo_id=grupo_id)

@usuario_obrigatorio
def meus_grupos_administrados(request):
    # Filtra os grupos onde o usuário logado é um dos administradores
    grupos = Grupo.objects.filter(administradores=request.user).order_by('-data_criacao')
    
    return render(request, "meus_grupos.html", {'grupos': grupos})