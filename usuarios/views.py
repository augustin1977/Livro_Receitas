from django.shortcuts import render
from django.http import HttpResponse

def login(requeste):
    return HttpResponse("Login de Usuário")

def cadastro(requeste):
    return HttpResponse("Cadastro de Usuário")

def editar(requeste):
    return HttpResponse("Editar Perfil de Usuário")

