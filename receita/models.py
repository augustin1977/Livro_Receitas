from django.db import models
from django.db.models.functions import Lower, Trim
from usuarios.models import Usuario

class Unidade(models.Model):

    unidades = models.CharField(max_length=60) # Ex: Quilograma, Grama

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower(Trim("unidades")),
                name="unidade_nome_unico_case_insensitive",
            )
        ]
    
    def __str__(self):
        return self.unidades

class Material(models.Model):
    nome = models.CharField(max_length=150)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower(Trim("nome")),
                name="material_nome_unico_case_insensitive",
            )
        ]

    def __str__(self):
        return self.nome

class Receita(models.Model):
    nome = models.CharField(max_length=150)
    modo_de_fazer = models.TextField()
    data_cadastro = models.DateTimeField(auto_now_add=True) 
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    favoritos = models.ManyToManyField(Usuario, related_name="receitas_favoritas", blank=True)

    def __str__(self):
        return f"Receita: {self.nome} (Autor: {self.usuario.username})"

class Ingrediente(models.Model):
    receita = models.ForeignKey(Receita, on_delete=models.PROTECT, related_name='ingredientes',null=True)
    material = models.ForeignKey(Material, on_delete=models.PROTECT,null=True)
    unidade=models.ForeignKey(Unidade, on_delete=models.PROTECT,null=True)
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        # Acessa os dados diretamente pelos relacionamentos, sem consultas extras
        return f" {self.quantidade} {self.unidade} de {self.material.nome} - "
