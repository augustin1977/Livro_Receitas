from django.urls import path
from . import views



urlpatterns = [
    path("valida_cadastro_material/",views.valida_cadastro_material,name="valida_cadastro_material"),
    path("cadastrar_receita/", views.cadastrar_receita,name="cadastrar_receita"),
    path("cadastrar_unidade/", views.cadastrar_unidade),
    path("cadastrar_material/", views.cadastrar_material),
    path("cadastrar_ingrediente/", views.cadastrar_ingrediente),
    path("home/",views.home, name="home"),
    path("mostrar_receita/",views.mostrar_receita, name="mostrar_receita"),
    
]
