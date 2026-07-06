from django.db import models
from usuarios.models import Usuario
from receita.models import Receita

class Comentario(models.Model):
    receita = models.ForeignKey(Receita, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    class Meta:
            ordering = ['-data_criacao']  # O sinal de menos indica ordem decrescente
    def __str__(self):
        return f"Comentário de {self.usuario.username} na receita {self.receita.nome}"
