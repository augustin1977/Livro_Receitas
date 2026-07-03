from django.urls import path
from . import views
# cria os caminhos para acesso as views
urlpatterns = [
    path("", views.login),
    path("cadastrar/",views.cadastrar, name="cadastrar"),
    path("editar/",views.editar, name="editar"),
    path("login/",views.login,name="login"),
    path("valida_cadastro/",views.valida_cadastro, name="valida_cadastro"),
    path("validar_login/",views.validar_login, name="validar_login"),
    path("sair/",views.sair, name="sair"),
    path('grupo/novo/', views.cadastrar_grupo, name='cadastrar_grupo'),
    path('grupo/gerenciar/<int:grupo_id>/', views.gerenciar_grupo, name='gerenciar_grupo'),
    path('grupo/adicionar-membro/<int:grupo_id>/', views.adicionar_membro, name='adicionar_membro'),
    path('grupo/meus-grupos/', views.meus_grupos_administrados, name='meus_grupos_administrados'),
    path('grupo/sair/<int:grupo_id>/', views.sair_do_grupo, name='sair_do_grupo'),
    path('grupo/<int:grupo_id>/remover-membro/<int:usuario_id>/', views.remover_membro, name='remover_membro'),
    path('grupo/adicionar-membro/<int:grupo_id>/', views.adicionar_membro, name='adicionar_membro'),
    path('grupo/convites/', views.meus_convites, name='meus_convites'),
    path('grupo/convites/responder/<int:convite_id>/<str:acao>/', views.responder_convite, name='responder_convite'),
    path('grupo/<int:grupo_id>/promover/<int:usuario_id>/', views.promover_administrador, name='promover_administrador'),
    path('grupo/<int:grupo_id>/revogar/<int:usuario_id>/', views.revogar_administrador, name='revogar_administrador'),
    path('grupo/excluir/<int:grupo_id>/', views.excluir_grupo, name='excluir_grupo'),
    path("alterar-senha/", views.alterar_senha, name="alterar_senha"),
    path("esqueci-senha/", views.esqueci_senha, name="esqueci_senha"),
    path("trocar-senha-obrigatoria/", views.trocar_senha_obrigatoria, name="trocar_senha_obrigatoria"),
    path("excluir-conta/", views.excluir_conta, name="excluir_conta"),
    path("usuarios/", views.listar_usuarios, name="listar_usuarios"),
    path("usuarios/excluir/<int:usuario_id>/", views.excluir_usuario_admin, name="excluir_usuario_admin"),
  
]
