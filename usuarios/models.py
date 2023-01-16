from django.db import models

class Usuario(models.Model):
    nome=models.CharField(max_length=50)
    email=models.EmailField(max_length=254)
    senha=models.CharField(max_length=64)
    tipo = models.CharField(max_length=10)
    def __str__(self):
        return self.nome