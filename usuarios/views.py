from django.shortcuts import render
from django.http import HttpResponse

def login(request):
    return render(request, "login.html")

def cadastrar(request):
    return render(request, "cadastro.html")

def editar(request):
    return render(request, "editar.html")

