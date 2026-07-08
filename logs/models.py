from django.db import models
from usuarios.models import Usuario


class LogAtividade(models.Model):
    
    ACOES_CHOICES = [
        ("CRIAR_RECEITA", "Criou a receita"),
        ("COPIAR_RECEITA", "Copiou a receita"),
        ("EDITAR_RECEITA", "Editou a receita"),
        ("EXCLUIR_RECEITA", "Excluiu a receita"),
        ("ADICIONAR_INGREDIENTE_RECEITA", "Adicionou ingrediente na receita"),
        ("EDITAR_INGREDIENTE_RECEITA", "Editou ingrediente da receita"),
        ("REMOVER_INGREDIENTE_RECEITA", "Removeu ingrediente da receita"),
        ("CRIAR_COMENTARIO", "Criou o comentario"),
        ("EDITAR_COMENTARIO", "Editou o comentario"),
        ("EXCLUIR_COMENTARIO", "Excluiu o comentario"),
        ("FAVORITAR", "Favoritou a receita"),
        ("DESFAVORITAR", "Removeu a receita dos favoritos"),
        ("CRIAR_UNIDADE", "Criou a unidade"),
        ("EDITAR_UNIDADE", "Editou a unidade"),
        ("EXCLUIR_UNIDADE", "Excluiu a unidade"),
        ("CRIAR_MATERIAL", "Criou o ingrediente"),
        ("EDITAR_MATERIAL", "Editou o ingrediente"),
        ("EXCLUIR_MATERIAL", "Excluiu o ingrediente"),
        ("CRIAR_GRUPO", "Criou o grupo"),
        ("EXCLUIR_GRUPO", "Excluiu o grupo"),
        ("ENVIAR_CONVITE_GRUPO", "Enviou convite de grupo"),
        ("ACEITAR_CONVITE_GRUPO", "Aceitou convite de grupo"),
        ("RECUSAR_CONVITE_GRUPO", "Recusou convite de grupo"),
        ("SAIR_GRUPO", "Saiu do grupo"),
        ("REMOVER_MEMBRO", "Removeu membro do grupo"),
        ("PROMOVER_ADMIN_GRUPO", "Promoveu administrador de grupo"),
        ("REVOGAR_ADMIN_GRUPO", "Revogou administrador de grupo"),
        ("CADASTRAR_USUARIO", "Cadastrou-se na plataforma"),
        ("EDITAR_USUARIO", "Editou usuario"),
        ("EXCLUIR_USUARIO", "Excluiu usuario"),
        ("ALTERAR_SENHA", "Alterou a senha de acesso"),
    ]
    usuario = models.ForeignKey(
        Usuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="logs_atividades",
    )
    acao = models.CharField(max_length=50, choices=ACOES_CHOICES)
    texto_jornal = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    id_objeto_alvo = models.IntegerField(null=True, blank=True)
    dados_anteriores = models.JSONField(null=True, blank=True)
    dados_novos = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.texto_jornal} em {self.data}"
