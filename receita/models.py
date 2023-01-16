from django.db import models
from django.contrib.auth.models import User

class Unidades(models.Model):
    simbolo=models.CharField( max_length=10)
    unidades=models.CharField(max_length=10)
    def __str__(self):
        return f"{self.unidades}"

class Materiais(models.Model):
    nome=models.CharField( max_length=150)
    unidade=models.ForeignKey(Unidades, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.nome} em {self.unidade}"


class Ingediente(models.Model):
    nome=models.ForeignKey(Materiais, on_delete=models.CASCADE)
    quantidade=models.DecimalField( max_digits=12, decimal_places=2)
    def __str__(self):
        return f"{self.nome}"


class Receita(models.Model):
    nome=models.CharField(max_length=150)
    ingredientes=models.ManyToManyField(Ingediente)
    modo_de_fazer=models.TextField()
    data_cadastro=models.DateTimeField( auto_now=True, auto_now_add=False)
    usuario=models.ForeignKey(User,on_delete=models.PROTECT)
    def __str__(self):
        return f"{self.nome} do {self.usuario} na data {self.data_cadastro}"
# comentário so para criar novo branch testando
# novo comentário

   
    
