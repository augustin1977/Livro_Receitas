from django.urls import path
from . import views



urlpatterns = [
    path("cadastrar/",views.cadastrar),
    path("cadastrar_receita/", views.cadastrar_receita),
    path("cadastrar_unidade/", views.cadastrar_unidade),
    path("cadastrar_material/", views.cadastrar_material),
    path("cadastrar_ingrediente/", views.cadastrar_ingrediente),
    path("home/",views.home, name="home")
    
]
