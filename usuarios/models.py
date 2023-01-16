from django.db import models
class Tipos(models.Model):
    """ Cria os tipos de usuário"""
    tipo = models.CharField(max_length=20)
    def __str__(self):
        return self.tipo
class Usuario(models.Model):
    """ Cria a classe usuario com todas as configurações de usuário"""
    nome=models.CharField(max_length=50)
    email=models.EmailField(max_length=254)
    senha=models.CharField(max_length=64)
    tipo = models.ForeignKey(Tipos,on_delete=models.PROTECT)
    def __str__(self):
        return self.nome