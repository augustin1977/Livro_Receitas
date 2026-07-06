from django.urls import path
from . import views

urlpatterns = [
    path('receita/<int:receita_id>/comentario/', views.adicionar_comentario, name='adicionar_comentario'),
    path('comentario/<int:comentario_id>/editar/', views.editar_comentario, name='editar_comentario'),
    path('comentario/<int:comentario_id>/excluir/', views.excluir_comentario, name='excluir_comentario'),
]