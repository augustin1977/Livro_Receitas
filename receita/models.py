from django.db import models
from usuarios.models import Usuario

class Unidade(models.Model):
    simbolo = models.CharField(max_length=10) # Ex: kg, g, ml
    unidades = models.CharField(max_length=50) # Ex: Quilograma, Grama
    
    def __str__(self):
        return self.unidades

class Material(models.Model):
    nome = models.CharField(max_length=150)
    # Mudança para PROTECT para evitar apagar uma unidade usada por um material

    def __str__(self):
        return self.nome

class Receita(models.Model):
    nome = models.CharField(max_length=150)
    modo_de_fazer = models.TextField()
    # auto_now_add=True define a data na criação. auto_now=True atualiza a cada edição.
    data_cadastro = models.DateTimeField(auto_now_add=True) 
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)

    def __str__(self):
        return f"Receita: {self.nome} (Autor: {self.usuario.username})"

class Ingrediente(models.Model):
    # Vincula o ingrediente diretamente a uma receita específica
    receita = models.ForeignKey(Receita, on_delete=models.PROTECT, related_name='ingredientes',null=True)
    material = models.ForeignKey(Material, on_delete=models.PROTECT,null=True)
    unidade=models.ForeignKey(Unidade, on_delete=models.PROTECT,null=True)
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        # Acessa os dados diretamente pelos relacionamentos, sem consultas extras
        return f" {self.quantidade} {self.unidade} de {self.material.nome} - "