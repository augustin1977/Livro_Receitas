from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from receita.models import Receita
from usuarios.models import Grupo

from .models import Comentario


class ComentarioPermissaoTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.alice = Usuario.objects.create_user(username="alice", password="senha123")
        self.bruno = Usuario.objects.create_user(username="bruno", password="senha123")
        self.clara = Usuario.objects.create_user(username="clara", password="senha123")

        self.grupo = Grupo.objects.create(nome="Familia")
        self.grupo.membros.add(self.alice, self.bruno)

        self.receita_bruno = Receita.objects.create(
            nome="Pao do Bruno",
            modo_de_fazer="Asse bem.",
            usuario=self.bruno,
        )
        self.receita_clara = Receita.objects.create(
            nome="Sopa da Clara",
            modo_de_fazer="Cozinhe devagar.",
            usuario=self.clara,
        )

    def test_usuario_comenta_receita_visivel(self):
        self.client.force_login(self.alice)

        resposta = self.client.post(
            reverse("adicionar_comentario", args=[self.receita_bruno.id]),
            {"texto": "Ficou otima."},
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            Comentario.objects.filter(
                receita=self.receita_bruno,
                usuario=self.alice,
                texto="Ficou otima.",
            ).exists()
        )

    def test_usuario_nao_comenta_receita_invisivel(self):
        self.client.force_login(self.alice)

        resposta = self.client.post(
            reverse("adicionar_comentario", args=[self.receita_clara.id]),
            {"texto": "Tentativa indevida."},
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(
            Comentario.objects.filter(
                receita=self.receita_clara,
                usuario=self.alice,
            ).exists()
        )

    def test_autor_edita_proprio_comentario_em_receita_visivel(self):
        comentario = Comentario.objects.create(
            receita=self.receita_bruno,
            usuario=self.alice,
            texto="Antes",
        )
        self.client.force_login(self.alice)

        resposta = self.client.post(
            reverse("editar_comentario", args=[comentario.id]),
            {"texto": "Depois"},
        )

        comentario.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(comentario.texto, "Depois")

    def test_usuario_nao_edita_comentario_de_outra_pessoa(self):
        comentario = Comentario.objects.create(
            receita=self.receita_bruno,
            usuario=self.alice,
            texto="Original",
        )
        self.client.force_login(self.bruno)

        resposta = self.client.post(
            reverse("editar_comentario", args=[comentario.id]),
            {"texto": "Alterado sem permissao"},
        )

        comentario.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(comentario.texto, "Original")
