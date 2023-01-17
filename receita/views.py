from django.shortcuts import render,redirect
from django.http import HttpResponse
from usuarios.models import Usuario
from .models import *
def cadastrar_receita(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    materiais= Materiais.objects.all()
    usuarios=Usuario.objects.all()
    return render(request,"cadastroReceita.html", {'materiais':materiais,'usuarios':usuarios})
def cadastrar_unidade(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    return HttpResponse("Cadastro Unidade")
def cadastrar_material(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    return HttpResponse("Cadastro Material")
def cadastrar_ingrediente(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    return HttpResponse("Cadastro Ingrediente")
def valida_cadastro_material(request):# falta finalizar implementação
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    nome=request.POST.get('nome')
    modoPreparo=request.POST.get('ModoPreparo')
    recebe_ingredientes=(request.POST.get('IngredientesSelecionados')).split("\n")
    ingredientes=[]
    for processa_dados in recebe_ingredientes:
        processa_dados=processa_dados.replace("\r","")
        processa_dados=processa_dados.replace("\t","")
        processa_dados=processa_dados.strip(" ")
        temp=processa_dados.split(";")
        ingredientes.append({'ingrediente':temp[0].strip(),'quantidade':temp[1].strip()})
    print(nome,ingredientes,modoPreparo)
    # ja tem os dados do formulário de cadastro sendo nome, modo de preparo e vetor com os ingredientes
    # falta implmentar a criação dos objetos e salvar no banco
    return HttpResponse("Olá")

def mostrar_receita(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    receita_id=int(request.GET.get('receita'))
    receita= Receita.objects.get(id=receita_id)
    receita.ingredientes_copy=Ingrediente.objects.filter(receita__id=receita_id)
    print(receita.ingredientes_copy)
    return render(request,"mostrar_receita.html", {'receita':receita})
def home(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    usuario=Usuario.objects.get(id=request.session['usuario'])
    receitas=list(Receita.objects.filter(usuario=usuario))
    return render(request,"home.html", {'Receitas':receitas})