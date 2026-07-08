from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import Grupo
from logs.models import LogAtividade

from .models import Ingrediente, Material, Receita, Unidade
from .selectors import receitas_visiveis_para
from .utils import (
    nomes_equivalentes,
    normalizar_nome_catalogo,
    normalizar_nome_para_comparacao,
    normalizar_nome_para_ordenacao,
    ordenar_objetos_por_nome,
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


class CopiarReceitaTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.alice = Usuario.objects.create_user(username="alice", password="senha123")
        self.bruno = Usuario.objects.create_user(username="bruno", password="senha123")
        self.clara = Usuario.objects.create_user(username="clara", password="senha123")
        self.grupo = Grupo.objects.create(nome="Familia")
        self.grupo.membros.add(self.alice, self.bruno)
        self.data_original = timezone.now() - timedelta(days=3650)
        self.unidade = Unidade.objects.create(unidades="Grama copia")
        self.material = Material.objects.create(nome="Farinha copia")
        self.receita_original = Receita.objects.create(
            nome="Receita historica",
            modo_de_fazer="Misture tudo.",
            data_cadastro=self.data_original,
            usuario=self.alice,
        )
        Ingrediente.objects.create(
            receita=self.receita_original,
            material=self.material,
            unidade=self.unidade,
            quantidade=Decimal("200"),
        )

    def test_copia_receita_completa_preservando_credito_e_data_original(self):
        self.client.force_login(self.bruno)

        resposta = self.client.post(
            reverse("copiar_receita", args=[self.receita_original.id])
        )

        self.assertEqual(resposta.status_code, 302)
        copia = Receita.objects.exclude(id=self.receita_original.id).get()
        self.assertEqual(copia.usuario, self.bruno)
        self.assertEqual(copia.criador_original, self.alice)
        self.assertEqual(copia.data_cadastro, self.receita_original.data_cadastro)
        self.assertGreater(copia.data_ultima_modificacao, copia.data_cadastro)
        ingrediente = copia.ingredientes.get()
        self.assertEqual(ingrediente.material, self.material)
        self.assertEqual(ingrediente.unidade, self.unidade)
        self.assertEqual(ingrediente.quantidade, Decimal("200"))
        self.assertTrue(
            LogAtividade.objects.filter(
                acao="COPIAR_RECEITA",
                usuario=self.bruno,
                id_objeto_alvo=copia.id,
            ).exists()
        )

    def test_copia_e_independente_da_receita_original(self):
        self.client.force_login(self.bruno)
        self.client.post(reverse("copiar_receita", args=[self.receita_original.id]))
        copia = Receita.objects.exclude(id=self.receita_original.id).get()

        copia.nome = "Minha versao"
        copia.modo_de_fazer = "Outro preparo."
        copia.save()
        ingrediente_copia = copia.ingredientes.get()
        ingrediente_copia.quantidade = Decimal("350")
        ingrediente_copia.save()

        self.receita_original.refresh_from_db()
        ingrediente_original = self.receita_original.ingredientes.get()
        self.assertEqual(self.receita_original.nome, "Receita historica")
        self.assertEqual(self.receita_original.modo_de_fazer, "Misture tudo.")
        self.assertEqual(ingrediente_original.quantidade, Decimal("200"))

    def test_copia_de_copia_mantem_a_primeira_autora_e_data(self):
        self.client.force_login(self.bruno)
        self.client.post(reverse("copiar_receita", args=[self.receita_original.id]))
        copia_bruno = Receita.objects.exclude(id=self.receita_original.id).get()
        self.grupo.membros.add(self.clara)
        self.client.force_login(self.clara)

        self.client.post(reverse("copiar_receita", args=[copia_bruno.id]))

        copia_clara = Receita.objects.filter(usuario=self.clara).get()
        self.assertEqual(copia_clara.criador_original, self.alice)
        self.assertEqual(copia_clara.data_cadastro, self.data_original)

    def test_nao_permite_copiar_receita_fora_dos_grupos(self):
        self.client.force_login(self.clara)

        resposta = self.client.post(
            reverse("copiar_receita", args=[self.receita_original.id])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Receita.objects.filter(usuario=self.clara).exists())

    def test_edicao_atualiza_data_da_versao(self):
        data_antiga = timezone.now() - timedelta(days=2)
        Receita.objects.filter(pk=self.receita_original.pk).update(
            data_ultima_modificacao=data_antiga
        )
        self.client.force_login(self.alice)

        self.client.post(
            f"{reverse('editar_receita')}?receita={self.receita_original.id}",
            {
                "nome": "Receita historica revisada",
                "ModoPreparo": "Misture e asse.",
                "IngredientesSelecionados": (
                    f"{self.material.id};200;{self.unidade.id}"
                ),
            },
        )

        self.receita_original.refresh_from_db()
        self.assertGreater(
            self.receita_original.data_ultima_modificacao,
            data_antiga,
        )
        self.assertEqual(self.receita_original.data_cadastro, self.data_original)


class HomeAtividadesJornalTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.alice = Usuario.objects.create_user(username="alice", password="senha123")
        self.bruno = Usuario.objects.create_user(username="bruno", password="senha123")
        self.clara = Usuario.objects.create_user(username="clara", password="senha123")

        self.grupo = Grupo.objects.create(nome="Familia")
        self.grupo.membros.add(self.alice, self.bruno)

    def test_home_mostra_ultimas_5_atividades_da_rede(self):
        for indice in range(7):
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
        self.assertEqual(len(atividades), 5)
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

    def test_home_nao_usa_permissao_admin_para_mostrar_feed_global(self):
        Usuario = get_user_model()
        admin = Usuario.objects.create_user(
            username="admin",
            password="senha123",
            is_staff=True,
        )
        receita_invisivel = Receita.objects.create(
            nome="Receita distante",
            modo_de_fazer="Prepare.",
            usuario=self.clara,
        )
        LogAtividade.objects.create(
            usuario=self.clara,
            acao="CRIAR_RECEITA",
            texto_jornal="clara criou a receita distante",
            id_objeto_alvo=receita_invisivel.id,
        )

        self.client.force_login(admin)
        resposta = self.client.get(reverse("home"))

        textos = [atividade["texto"] for atividade in resposta.context["atividades_jornal"]]
        self.assertNotIn("clara publicou a receita 'Receita distante'", textos)

    def test_home_ignora_grupo_tecnico_sem_familia_no_feed(self):
        grupo_tecnico = Grupo.objects.create(nome="Sem_Familia")
        grupo_tecnico.membros.add(self.alice, self.clara)
        receita_invisivel = Receita.objects.create(
            nome="Receita do grupo tecnico",
            modo_de_fazer="Prepare.",
            usuario=self.clara,
        )
        LogAtividade.objects.create(
            usuario=self.clara,
            acao="CRIAR_RECEITA",
            texto_jornal="clara criou a receita do grupo tecnico",
            id_objeto_alvo=receita_invisivel.id,
        )

        self.client.force_login(self.alice)
        resposta = self.client.get(reverse("home"))

        textos = [atividade["texto"] for atividade in resposta.context["atividades_jornal"]]
        self.assertNotIn("clara publicou a receita 'Receita do grupo tecnico'", textos)


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

    def test_ordena_ingredientes_sem_diferenciar_acentos(self):
        materiais = ordenar_objetos_por_nome(
            [
                Material(nome="Xilitol"),
                Material(nome="Orégano"),
                Material(nome="Óleo de soja"),
                Material(nome="Cebola"),
            ],
            "nome",
        )

        self.assertEqual(
            [material.nome for material in materiais],
            ["Cebola", "Óleo de soja", "Orégano", "Xilitol"],
        )

    def test_normalizacao_para_ordenacao_preserva_espacos(self):
        self.assertEqual(
            normalizar_nome_para_ordenacao("  ÓLEO   de Soja "),
            "oleo de soja",
        )

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
