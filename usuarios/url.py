from django.urls import path
from . import views
# cria os caminhos para acesso as views
urlpatterns = [
    path("", views.login),
    path("cadastrar/",views.cadastrar, name="cadastrar"),
    path("editar/",views.editar, name="editar_usuarios"),
    path("login/",views.login,name="login"),
    path("valida_cadastro/",views.valida_cadastro, name="valida_cadastro"),
    path("validar_login/",views.validar_login, name="validar_login"),
    path("sair/",views.sair, name="sair"),
    path('grupo/novo/', views.cadastrar_grupo, name='cadastrar_grupo'),
    path('grupo/gerenciar/<int:grupo_id>/', views.gerenciar_grupo, name='gerenciar_grupo'),
    path('grupo/adicionar-membro/<int:grupo_id>/', views.adicionar_membro, name='adicionar_membro'),
    path('grupo/meus-grupos/', views.meus_grupos_administrados, name='meus_grupos_administrados'),
]
