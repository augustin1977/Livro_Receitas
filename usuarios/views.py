from django.shortcuts import render
from django.http import HttpResponse
from .models import Usuario
from django.shortcuts import redirect 
from hashlib import sha256

def login(request):
    status=str(request.GET.get('status'))
    return render(request, "login.html", {'status':status})

def cadastrar(request):
    status=str(request.GET.get('status'))
    return render(request, "cadastro.html", {'status':status})

def editar(request):
    return render(request, "editar.html")

def valida_cadastro(request):
    nome=request.POST.get('nome')
    email=request.POST.get('email')
    senha=request.POST.get('senha')
    
    tipo="user"
    usuario= Usuario.objects.filter(email=email)
    if len(usuario)>0:
        return redirect('/auth/cadastrar/?status=1') # retorna erro de usuario ja existente
    usuario= Usuario.objects.filter(nome=nome)
    if len(usuario)>0:
        return redirect('/auth/cadastrar/?status=1') # retorna erro de usuario ja existente
    if len(nome.strip())==0 or len(email.strip())==0 :
        return redirect('/auth/cadastrar/?status=2') # retorna erro valor nulo
    if len(senha.strip())<8:
        return redirect('/auth/cadastrar/?status=3') # Senha muito curta
    try:
        senha= sha256(senha.encode()).hexdigest() # recuperando senha e codificando num hash sha256
        usuario=Usuario(nome=nome, senha=senha, email=email, tipo=tipo)
        usuario.save()
        return redirect('/auth/login/?status=0') # retorna sem erro
    except:
        pass
        return redirect('/auth/cadastro/?status=3') # retorna erro geral de gravação no banco de dados
    return HttpResponse("Erro na pagina de cadastro - View")

def validar_login(request):
    email=request.POST.get('email')
    senha=request.POST.get('senha')
    senha=sha256(senha.encode()).hexdigest()
    usuario=Usuario.objects.filter(email=email).filter(senha=senha)
    if len(usuario)==0:
        return redirect('/auth/login/?status=1')
    else:
        request.session['usuario']= usuario[0].id
        return redirect(f'/receita/home/')
    
def sair(request):
    request.session.flush()
    return redirect('/auth/login')
