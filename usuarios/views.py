"""Compatibilidade para URLs existentes.

As views foram separadas por responsabilidade, mas este modulo continua
reexportando os mesmos nomes para evitar mudanca nas rotas atuais.
"""

from .permissions import usuario_administra_grupo, usuario_e_admin_geral
from .views_auth import (
    alterar_senha,
    esqueci_senha,
    login,
    sair,
    trocar_senha_obrigatoria,
    validar_login,
)
from .views_conta import (
    cadastrar,
    editar,
    excluir_conta,
    excluir_usuario_admin,
    listar_usuarios,
    valida_cadastro,
)
from .views_grupos import (
    adicionar_membro,
    cadastrar_grupo,
    excluir_grupo,
    gerenciar_grupo,
    meus_convites,
    meus_grupos_administrados,
    promover_administrador,
    remover_membro,
    responder_convite,
    revogar_administrador,
    sair_do_grupo,
)

__all__ = [
    "adicionar_membro",
    "alterar_senha",
    "cadastrar",
    "cadastrar_grupo",
    "editar",
    "esqueci_senha",
    "excluir_conta",
    "excluir_grupo",
    "excluir_usuario_admin",
    "gerenciar_grupo",
    "listar_usuarios",
    "login",
    "meus_convites",
    "meus_grupos_administrados",
    "promover_administrador",
    "remover_membro",
    "responder_convite",
    "revogar_administrador",
    "sair",
    "sair_do_grupo",
    "trocar_senha_obrigatoria",
    "usuario_administra_grupo",
    "usuario_e_admin_geral",
    "valida_cadastro",
    "validar_login",
]
