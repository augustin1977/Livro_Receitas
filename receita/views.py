from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def cadastrar_receita(requeste):
    return HttpResponse("Cadastro Receita")
def cadastrar_unidade(requeste):
    return HttpResponse("Cadastro Unidade")
def cadastrar_material(requeste):
    return HttpResponse("Cadastro Material")
def cadastrar_ingrediente(requeste):
    return HttpResponse("Cadastro Ingrediente")


def cadastrar(request):
    return HttpResponse("Olá")