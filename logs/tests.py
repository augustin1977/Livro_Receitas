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
        self.assertIsNone(log.dados_novos)
        self.assertIn("alice", log.texto_jornal)
        self.assertIn("Bolo simples", log.texto_jornal)

    def test_registrar_log_descreve_edicao_de_receita(self):
        registrar_log(
            usuario=self.usuario,
            acao="EDITAR_RECEITA",
            id_objeto_alvo=10,
            nome_objeto="Agua quente",
            dados_anteriores={
                "nome": "Agua morna",
                "modo_de_fazer": "Aquecer pouco.",
            },
            dados_novos={
                "nome": "Agua quente",
                "modo_de_fazer": "Aquecer ate ferver.",
            },
        )

        log = LogAtividade.objects.get()
        self.assertIn("nome mudou de 'Agua morna' para 'Agua quente'", log.texto_jornal)
        self.assertIn(
            "modo de preparo mudou de 'Aquecer pouco.' para 'Aquecer ate ferver.'",
            log.texto_jornal,
        )

    def test_registrar_log_descreve_conteudo_do_comentario(self):
        registrar_log(
            usuario=self.usuario,
            acao="CRIAR_COMENTARIO",
            id_objeto_alvo=10,
            nome_objeto="Agua quente",
            dados_novos={"texto": "Ficou muito boa."},
        )

        log = LogAtividade.objects.get()
        self.assertIn("Agua quente", log.texto_jornal)
        self.assertIn("Ficou muito boa.", log.texto_jornal)

    def test_registrar_log_ignora_usuario_vazio(self):
        registrar_log(usuario=None, acao="CRIAR_RECEITA")

        self.assertEqual(LogAtividade.objects.count(), 0)

    def test_log_permanece_quando_usuario_e_excluido(self):
        registrar_log(
            usuario=self.usuario,
            acao="CRIAR_RECEITA",
            id_objeto_alvo=10,
            nome_objeto="Bolo simples",
        )

        self.usuario.delete()

        log = LogAtividade.objects.get()
        self.assertIsNone(log.usuario)
        self.assertIn("alice", log.texto_jornal)


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
            acao="CRIAR_RECEITA",
            texto_jornal="admin criou a receita",
        )
        LogAtividade.objects.create(
            usuario=self.admin,
            acao="CRIAR_COMENTARIO",
            texto_jornal="admin criou o comentario",
        )

    def test_usuario_comum_nao_acessa_painel_de_logs(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("painel_administrador_logs"))

        self.assertEqual(resposta.status_code, 302)

    def test_admin_acessa_painel_de_logs_filtrado(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(
            reverse("painel_administrador_logs"),
            {"acao": "COMENTARIO"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["acao_filtro"], "COMENTARIO")
        logs = list(resposta.context["logs"])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].acao, "CRIAR_COMENTARIO")
        self.assertContains(
            resposta,
            "acao=COMENTARIO\" class=\"btn btn-sm btn-dark\"",
        )
