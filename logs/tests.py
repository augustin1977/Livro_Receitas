from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import LogAtividade
from .utils import registrar_log


class RegistrarLogTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.usuario = Usuario.objects.create_user(
            username="alice",
            password="senha123",
        )

    def test_registrar_log_cria_texto_de_auditoria(self):
        registrar_log(
            usuario=self.usuario,
            acao="CRIAR_RECEITA",
            id_objeto_alvo=10,
            nome_objeto="Bolo simples",
            dados_anteriores={"nome": "Bolo antigo"},
        )

        log = LogAtividade.objects.get()
        self.assertEqual(log.usuario, self.usuario)
        self.assertEqual(log.acao, "CRIAR_RECEITA")
        self.assertEqual(log.id_objeto_alvo, 10)
        self.assertEqual(log.dados_anteriores, {"nome": "Bolo antigo"})
        self.assertIn("alice", log.texto_jornal)
        self.assertIn("Bolo simples", log.texto_jornal)

    def test_registrar_log_ignora_usuario_vazio(self):
        registrar_log(usuario=None, acao="LOGIN")

        self.assertEqual(LogAtividade.objects.count(), 0)


class PainelLogsTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.usuario = Usuario.objects.create_user(
            username="usuario",
            password="senha123",
        )
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="senha123",
            is_staff=True,
        )
        LogAtividade.objects.create(
            usuario=self.admin,
            acao="LOGIN",
            texto_jornal="admin entrou no sistema",
        )
        LogAtividade.objects.create(
            usuario=self.admin,
            acao="COMENTAR",
            texto_jornal="admin comentou na receita",
        )

    def test_usuario_comum_nao_acessa_painel_de_logs(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("painel_administrador_logs"))

        self.assertEqual(resposta.status_code, 302)

    def test_admin_acessa_painel_de_logs_filtrado(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(
            reverse("painel_administrador_logs"),
            {"acao": "COMENTAR"},
        )

        self.assertEqual(resposta.status_code, 200)
        logs = list(resposta.context["logs"])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].acao, "COMENTAR")
