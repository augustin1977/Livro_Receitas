from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Grupo
from logs.models import LogAtividade

from .models import Ingrediente, Material, Receita, Unidade
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


class HomeAtividadesJornalTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.alice = Usuario.objects.create_user(username="alice", password="senha123")
        self.bruno = Usuario.objects.create_user(username="bruno", password="senha123")
        self.clara = Usuario.objects.create_user(username="clara", password="senha123")

        self.grupo = Grupo.objects.create(nome="Familia")
        self.grupo.membros.add(self.alice, self.bruno)

    def test_home_mostra_ultimas_10_atividades_da_rede(self):
        for indice in range(12):
            receita = Receita.objects.create(
                nome=f"Receita {indice}",
                modo_de_fazer="Prepare.",
                usuario=self.bruno,
            )
            LogAtividade.objects.create(
                usuario=self.bruno,
                acao="CRIAR_RECEITA",
                texto_jornal=f"bruno criou a receita {indice}",
                id_objeto_alvo=receita.id,
                dados_novos={"receita_id": receita.id},
            )

        self.client.force_login(self.alice)
        resposta = self.client.get(reverse("home"))

        atividades = list(resposta.context["atividades_jornal"])
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(atividades), 10)
        self.assertTrue(all(atividade["url"] for atividade in atividades))
        self.assertTrue(all("publicou a receita" in atividade["texto"] for atividade in atividades))

    def test_home_nao_mostra_atividade_de_usuario_fora_da_rede(self):
        receita_visivel = Receita.objects.create(
            nome="Receita visivel",
            modo_de_fazer="Prepare.",
            usuario=self.bruno,
        )
        receita_invisivel = Receita.objects.create(
            nome="Receita invisivel",
            modo_de_fazer="Prepare.",
            usuario=self.clara,
        )
        LogAtividade.objects.create(
            usuario=self.bruno,
            acao="CRIAR_RECEITA",
            texto_jornal="bruno criou a receita visivel",
            id_objeto_alvo=receita_visivel.id,
        )
        LogAtividade.objects.create(
            usuario=self.clara,
            acao="CRIAR_RECEITA",
            texto_jornal="clara criou a receita invisivel",
            id_objeto_alvo=receita_invisivel.id,
        )

        self.client.force_login(self.alice)
        resposta = self.client.get(reverse("home"))

        textos = [atividade["texto"] for atividade in resposta.context["atividades_jornal"]]
        self.assertIn("bruno publicou a receita 'Receita visivel'", textos)
        self.assertNotIn("clara publicou a receita 'Receita invisivel'", textos)


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


class AuditoriaIngredientesReceitaTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.usuario = Usuario.objects.create_user(
            username="alice",
            password="senha123",
        )
        self.client.force_login(self.usuario)
        self.unidade = Unidade.objects.create(unidades="Grama teste")
        self.xicara = Unidade.objects.create(unidades="Xicara teste")
        self.acucar = Material.objects.create(nome="Acucar teste")
        self.sal = Material.objects.create(nome="Sal teste")
        self.receita = Receita.objects.create(
            nome="Bolo teste",
            modo_de_fazer="Misture.",
            usuario=self.usuario,
        )
        Ingrediente.objects.create(
            receita=self.receita,
            material=self.acucar,
            unidade=self.unidade,
            quantidade=Decimal("100"),
        )

    def test_audita_ingrediente_adicionado_na_edicao_da_receita(self):
        ingredientes = (
            f"{self.acucar.id};100;{self.unidade.id}\n"
            f"{self.sal.id};1;{self.xicara.id}"
        )

        resposta = self.client.post(
            f"{reverse('editar_receita')}?receita={self.receita.id}",
            {
                "nome": self.receita.nome,
                "ModoPreparo": self.receita.modo_de_fazer,
                "IngredientesSelecionados": ingredientes,
            },
        )

        self.assertEqual(resposta.status_code, 302)
        log = LogAtividade.objects.get(acao="ADICIONAR_INGREDIENTE_RECEITA")
        self.assertIn("Sal teste", log.texto_jornal)
        self.assertIn("1", log.texto_jornal)
        self.assertIn("Xicara teste", log.texto_jornal)

    def test_audita_ingrediente_removido_na_edicao_da_receita(self):
        ingredientes = f"{self.sal.id};1;{self.xicara.id}"

        resposta = self.client.post(
            f"{reverse('editar_receita')}?receita={self.receita.id}",
            {
                "nome": self.receita.nome,
                "ModoPreparo": self.receita.modo_de_fazer,
                "IngredientesSelecionados": ingredientes,
            },
        )

        self.assertEqual(resposta.status_code, 302)
        log = LogAtividade.objects.get(acao="REMOVER_INGREDIENTE_RECEITA")
        self.assertIn("Acucar teste", log.texto_jornal)
        self.assertIn("100", log.texto_jornal)
        self.assertIn("Grama teste", log.texto_jornal)

    def test_audita_ingrediente_alterado_na_edicao_da_receita(self):
        ingredientes = f"{self.acucar.id};2;{self.xicara.id}"

        resposta = self.client.post(
            f"{reverse('editar_receita')}?receita={self.receita.id}",
            {
                "nome": self.receita.nome,
                "ModoPreparo": self.receita.modo_de_fazer,
                "IngredientesSelecionados": ingredientes,
            },
        )

        self.assertEqual(resposta.status_code, 302)
        log = LogAtividade.objects.get(acao="EDITAR_INGREDIENTE_RECEITA")
        self.assertIn("Acucar teste", log.texto_jornal)
        self.assertIn("100 Grama teste", log.texto_jornal)
        self.assertIn("2 Xicara teste", log.texto_jornal)
