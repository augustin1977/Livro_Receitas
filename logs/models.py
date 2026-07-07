from django.db import models
from usuarios.models import Usuario

class LogAtividade(models.Model):
    ACOES_CHOICES = [
    ('CRIAR_RECEITA', 'Criou a receita'),
    ('EDITAR_RECEITA', 'Editou a receita'),
    ('EXCLUIR_RECEITA', 'Excluiu a receita'),
    ('COPIAR_RECEITA', 'Copiou a receita'),
    ('COMENTAR', 'Comentou na receita'),
    ('FAVORITAR', 'Favoritou a receita'),
    # Ações unidades
    ('CRIAR_UNIDADE','Criou a unidade'),
    ('EDITAR_UNIDADE','Editou a unidade'),
    ('EXCLUIR_UNIDADE','Excluiu a unidade'),
    # Novas Ações de Grupos
    ('CRIAR_GRUPO', 'Criou o grupo'),
    ('EXCLUIR_GRUPO', 'Excluiu o grupo'),
    ('ADICIONAR_MEMBRO', 'Adicionou membro ao grupo'),
    ('REMOVER_MEMBRO', 'Removeu membro do grupo'),
    # Novas Ações de Usuários
    ('CADASTRAR_USUARIO', 'Cadastrou-se na plataforma'),
    ('LOGIN', 'Entrou no sistema'),
    ('LOGOUT', 'Saiu do sistema'),
    ('ALTERAR_SENHA', 'Alterou a senha de acesso'),
    # Ação de Moderação
    ('DESFAZER_ACAO', 'Reverteu uma ação do sistema'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='logs_atividades')
    acao = models.CharField(max_length=50, choices=ACOES_CHOICES)
    texto_jornal = models.CharField(max_length=255)
    data = models.DateTimeField(auto_now_add=True)
    id_objeto_alvo = models.IntegerField(null=True, blank=True)
    dados_anteriores = models.JSONField(null=True, blank=True)
    foi_desfeito = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"{self.texto_jornal} em {self.data}"
    

