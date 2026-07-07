from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Grupo

from .models import Receita
from .selectors import receitas_visiveis_para


class ReceitasVisiveisParaTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.alice = Usuario.objects.create_user(username="alice", password="senha123")
        self.bruno = Usuario.objects.create_user(username="bruno", password="senha123")
        self.clara = Usuario.objects.create_user(username="clara", password="senha123")

        self.grupo = Grupo.objects.create(nome="Familia")
        self.grupo.membros.add(self.alice, self.bruno)

        self.receita_alice = Receita.objects.create(
            nome="Bolo da Alice",
            modo_de_fazer="Misture tudo.",
            usuario=self.alice,
        )
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

    def test_usuario_ve_receita_propria_e_de_membro_do_mesmo_grupo(self):
        receitas_ids = set(
            receitas_visiveis_para(self.alice).values_list("id", flat=True)
        )

        self.assertIn(self.receita_alice.id, receitas_ids)
        self.assertIn(self.receita_bruno.id, receitas_ids)

    def test_usuario_nao_ve_receita_de_fora_dos_grupos(self):
        receitas_ids = set(
            receitas_visiveis_para(self.alice).values_list("id", flat=True)
        )

        self.assertNotIn(self.receita_clara.id, receitas_ids)

    def test_usuario_nao_favorita_receita_invisivel(self):
        self.client.force_login(self.alice)

        resposta = self.client.post(
            reverse("favoritar_receita", args=[self.receita_clara.id])
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(self.receita_clara.favoritos.filter(id=self.alice.id).exists())
