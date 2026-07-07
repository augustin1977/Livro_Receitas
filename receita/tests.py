from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Grupo

from .models import Material, Receita, Unidade
from .selectors import receitas_visiveis_para
from .utils import (
    nomes_equivalentes,
    normalizar_nome_catalogo,
    normalizar_nome_para_comparacao,
)


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


class CatalogoReceitaTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="senha123",
            is_staff=True,
        )
        self.client.force_login(self.admin)

    def test_normaliza_nome_de_catalogo(self):
        self.assertEqual(
            normalizar_nome_catalogo("  acucar   refinado  "),
            "Acucar refinado",
        )

    def test_normaliza_nome_para_comparacao_sem_acentos_caixa_e_espacos(self):
        self.assertEqual(
            normalizar_nome_para_comparacao("  Xícara de chá  "),
            "xicaradecha",
        )
        self.assertTrue(nomes_equivalentes("Água", "agua"))
        self.assertTrue(nomes_equivalentes("Açúcar", "Acucar"))
        self.assertTrue(nomes_equivalentes("Xícara de chá", "XiCarádeChá"))

    def test_nao_cria_unidade_duplicada_pela_tela(self):
        Unidade.objects.create(unidades="Xícara de chá teste")

        resposta = self.client.post(
            reverse("gerenciar_unidades"),
            {"nome_unidade": "XiCarádeCháTeste"},
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(
            sum(
                1 for unidade in Unidade.objects.all()
                if nomes_equivalentes(unidade.unidades, "XiCarádeCháTeste")
            ),
            1,
        )

    def test_nao_cria_material_duplicado_pela_tela(self):
        Material.objects.create(nome="Água especial")

        resposta = self.client.post(
            reverse("gerenciar_ingredientes"),
            {"nome_ingrediente": "AguaEspecial"},
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(
            sum(
                1 for material in Material.objects.all()
                if nomes_equivalentes(material.nome, "AguaEspecial")
            ),
            1,
        )

    def test_nao_edita_unidade_para_nome_ja_existente(self):
        unidade_original = Unidade.objects.create(unidades="Unidade original")
        Unidade.objects.create(unidades="Xícara de chá existente")

        resposta = self.client.post(
            reverse("editar_unidade", args=[unidade_original.id]),
            {"nome_unidade": "XiCarádeCháExistente"},
        )

        unidade_original.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(unidade_original.unidades, "Unidade original")

    def test_nao_edita_material_para_nome_ja_existente(self):
        material_original = Material.objects.create(nome="Ingrediente original")
        Material.objects.create(nome="Açúcar existente")

        resposta = self.client.post(
            reverse("editar_ingrediente", args=[material_original.id]),
            {"nome_ingrediente": "AcucarExistente"},
        )

        material_original.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(material_original.nome, "Ingrediente original")

    def test_banco_rejeita_unidade_duplicada(self):
        Unidade.objects.create(unidades="Unidade banco")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Unidade.objects.create(unidades="  unidade banco  ")

    def test_banco_rejeita_material_duplicado(self):
        Material.objects.create(nome="Ingrediente banco")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Material.objects.create(nome="  ingrediente banco  ")
