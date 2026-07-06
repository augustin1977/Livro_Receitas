from django.urls import path
from . import views

urlpatterns = [
    path('admin-geral/logs/', views.painel_administrador_logs, name='painel_administrador_logs'),
    path('admin-geral/logs/<int:log_id>/desfazer/', views.desfazer_acao_log, name='desfazer_acao_log'),
]