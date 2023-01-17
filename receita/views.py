from django.shortcuts import render,redirect
from django.http import HttpResponse
from usuarios.models import Usuario
from .models import *
def cadastrar_receita(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    return HttpResponse("Cadastro Receita")
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
def cadastrar(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
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