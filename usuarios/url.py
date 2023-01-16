from django.urls import path
from . import views

urlpatterns = [
    path("cadastrar/",views.cadastrar, name="cadastro"),
    path("editar/",views.editar, name="editar_usuarios"),
    path("login/",views.login,name="login"),
    path("valida_cadastro/",views.valida_cadastro, name="valida_cadastro")
    
]