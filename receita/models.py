from django.db import models
from usuarios.models import Usuario
"""Classe unidades de medida, cadastrar a unidade de medida e seu simbolo ou abreveação"""
class Unidades(models.Model):
    simbolo=models.CharField( max_length=10)
    unidades=models.CharField(max_length=10)
    def __str__(self):
        return f"{self.unidades}"
"""Classe Materis cria o cadastro de materiais usados nas receitas"""
class Materiais(models.Model):
    nome=models.CharField( max_length=150)
    unidade=models.ForeignKey(Unidades, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.nome} em {self.unidade}"

""" Classe Ingredientes cria o cadastros de ingredientes usados em cada receita, ou seja é identico ao 
cadastro de materiais, no entanto tem a vinculação com a receita"""
class Ingrediente(models.Model):
    nome=models.ForeignKey(Materiais, on_delete=models.CASCADE)
    quantidade=models.DecimalField( max_digits=12, decimal_places=2)
    def __str__(self):
        return f"{self.nome} - {self. quantidade}"

"""Classe receita é onde ficam aramzenadas as receitas propriamente ditas"""
class Receita(models.Model):
    nome=models.CharField(max_length=150)
    ingredientes=models.ManyToManyField(Ingrediente)
    modo_de_fazer=models.TextField()
    data_cadastro=models.DateTimeField( auto_now=True, auto_now_add=False)
    usuario=models.ForeignKey(Usuario,on_delete=models.PROTECT)
    def __str__(self):
        return f"{self.nome} do {self.usuario} - {self.ingredientes}"


   
    
