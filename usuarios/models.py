from django.db import models
from django.contrib.auth.models import AbstractUser

class Tipo(models.Model):
    """ Cria os tipos de usuário"""
    tipo = models.CharField(max_length=20)
    def __str__(self):
        return self.tipo
class Usuario(AbstractUser):
    """ Cria a classe usuario com todas as configurações de usuário"""
    nome=models.CharField(max_length=50)
    foto=models.ImageField(upload_to='perfis/', null=True, blank=True)
    tipo = models.ForeignKey(Tipo,on_delete=models.DO_NOTHING,null=True, blank=True)
    def __str__(self):
        return self.nome
class Grupo (models.Model):
    nome = models.CharField(max_length=100)
    # related_name permite buscar as famílias de um usuário usando usuario.familias.all()
    membros = models.ManyToManyField(Usuario, related_name='grupos')
    administradores = models.ManyToManyField(Usuario, related_name='grupos_administrados')
    data_criacao = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.nome