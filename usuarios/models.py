from django.db import models
class Familia(models.Model):
    
    nomeFamilia = models.CharField(max_length=80)
    def __str__(self):
        return self.nomeFamilia
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
    tipo = models.ForeignKey(Tipos,on_delete=models.DO_NOTHING)
    nomeFamilia=models.ForeignKey(Familia,on_delete=models.DO_NOTHING)
    def __str__(self):
        return self.nome