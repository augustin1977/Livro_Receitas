from django.shortcuts import render,redirect
from django.http import HttpResponse

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
def home(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')
    return HttpResponse("Olá Home")