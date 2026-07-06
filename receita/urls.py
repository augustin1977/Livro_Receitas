from django.urls import path
from . import views



urlpatterns = [
    path("home/", views.home, name="home"),
    path("valida_cadastro_material/",views.valida_cadastro_material,name="valida_cadastro_material"),
    path("cadastrar_receita/", views.cadastrar_receita,name="cadastrar_receita"),
    path('unidades/', views.gerenciar_unidades, name='gerenciar_unidades'),
    path('unidades/editar/<int:pk>/', views.editar_unidade, name='editar_unidade'),
    path('unidades/excluir/<int:pk>/', views.excluir_unidade, name='excluir_unidade'),
    path("mostrar_receitas/",views.mostrar_receitas, name="mostrar_receitas"),
    path("mostrar_receita/",views.mostrar_receita, name="mostrar_receita"),
    path('confirmar-exclusao/', views.confirmar_exclusao, name='confirmar_exclusao'),
    path('excluir-receita/', views.excluir_receita, name='excluir_receita'),
    path('editar/', views.editar_receita, name='editar_receita'),
    path('ingredientes/', views.gerenciar_ingredientes, name='gerenciar_ingredientes'),
    path('ingredientes/editar/<int:pk>/', views.editar_ingrediente, name='editar_ingrediente'),
    path('ingredientes/excluir/<int:pk>/', views.excluir_ingrediente, name='excluir_ingrediente'),
    path("pesquisar/", views.pesquisar_receitas, name="pesquisar_receitas"),
]
