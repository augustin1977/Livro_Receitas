from django.urls import path
from . import views

urlpatterns = [
    path('admin-geral/logs/', views.painel_administrador_logs, name='painel_administrador_logs'),
]
