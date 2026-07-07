from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ConviteGrupo, Grupo, Tipo


class CadastroUsuarioTests(TestCase):
    def setUp(self):
        Tipo.objects.get_or_create(tipo="user")
        self.grupo_padrao, _ = Grupo.objects.get_or_create(nome="Sem_Familia")

    def test_cadastro_cria_usuario_com_tipo_padrao_e_grupo_padrao(self):
        resposta = self.client.post(
            reverse("valida_cadastro"),
            {
                "username": "maria",
                "nome": "Maria Silva",
                "email": "maria@example.com",
                "senha": "Senha1!",
            },
        )

        Usuario = get_user_model()
        usuario = Usuario.objects.get(username="maria")

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(usuario.tipo.tipo, "user")
        self.assertTrue(self.grupo_padrao.membros.filter(id=usuario.id).exists())

    def test_cadastro_rejeita_username_duplicado(self):
        Usuario = get_user_model()
        Usuario.objects.create_user(username="maria", password="Senha1!")

        resposta = self.client.post(
            reverse("valida_cadastro"),
            {
                "username": "maria",
                "nome": "Maria Silva",
                "email": "outra@example.com",
                "senha": "Senha1!",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Usuario.objects.filter(username="maria").count(), 1)


class ConviteGrupoTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.admin = Usuario.objects.create_user(username="admin", password="senha123")
        self.convidado = Usuario.objects.create_user(
            username="convidado",
            password="senha123",
        )
        self.grupo = Grupo.objects.create(nome="Familia")
        self.grupo.membros.add(self.admin)
        self.grupo.administradores.add(self.admin)
        self.convite = ConviteGrupo.objects.create(
            grupo=self.grupo,
            usuario_convidado=self.convidado,
        )

    def test_usuario_aceita_convite_e_vira_membro_do_grupo(self):
        self.client.force_login(self.convidado)

        resposta = self.client.get(
            reverse("responder_convite", args=[self.convite.id, "aceitar"])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(self.grupo.membros.filter(id=self.convidado.id).exists())
        self.assertFalse(ConviteGrupo.objects.filter(id=self.convite.id).exists())

    def test_usuario_recusa_convite_sem_entrar_no_grupo(self):
        self.client.force_login(self.convidado)

        resposta = self.client.get(
            reverse("responder_convite", args=[self.convite.id, "recusar"])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(self.grupo.membros.filter(id=self.convidado.id).exists())
        self.assertFalse(ConviteGrupo.objects.filter(id=self.convite.id).exists())


class AdministracaoGrupoPermissaoTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.admin_a = Usuario.objects.create_user(
            username="admin_a",
            password="senha123",
        )
        self.admin_geral = Usuario.objects.create_user(
            username="admin_geral",
            password="senha123",
            is_staff=True,
        )
        self.membro_a = Usuario.objects.create_user(
            username="membro_a",
            password="senha123",
        )
        self.membro_b = Usuario.objects.create_user(
            username="membro_b",
            password="senha123",
        )

        self.grupo_a = Grupo.objects.create(nome="Grupo A")
        self.grupo_a.membros.add(self.admin_a, self.membro_a)
        self.grupo_a.administradores.add(self.admin_a)

        self.grupo_b = Grupo.objects.create(nome="Grupo B")
        self.grupo_b.membros.add(self.membro_b)

    def test_admin_do_grupo_remove_membro_do_proprio_grupo(self):
        self.client.force_login(self.admin_a)

        resposta = self.client.get(
            reverse("remover_membro", args=[self.grupo_a.id, self.membro_a.id])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(self.grupo_a.membros.filter(id=self.membro_a.id).exists())

    def test_admin_de_um_grupo_nao_remove_membro_de_outro_grupo(self):
        self.client.force_login(self.admin_a)

        resposta = self.client.get(
            reverse("remover_membro", args=[self.grupo_b.id, self.membro_b.id])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(self.grupo_b.membros.filter(id=self.membro_b.id).exists())

    def test_admin_geral_pode_promover_membro_de_qualquer_grupo(self):
        self.client.force_login(self.admin_geral)

        resposta = self.client.get(
            reverse("promover_administrador", args=[self.grupo_b.id, self.membro_b.id])
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            self.grupo_b.administradores.filter(id=self.membro_b.id).exists()
        )
