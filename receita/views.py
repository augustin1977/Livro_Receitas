"""Compatibilidade para URLs existentes.

As views foram separadas por responsabilidade, mas este modulo continua
reexportando os mesmos nomes para evitar mudanca nas rotas atuais.
"""

from .auditoria import (
    auditar_mudancas_ingredientes_receita,
    dados_auditoria_ingrediente,
    dados_auditoria_ingrediente_existente,
)
from .views_catalogo import (
    editar_ingrediente,
    editar_unidade,
    excluir_ingrediente,
    excluir_unidade,
    gerenciar_ingredientes,
    gerenciar_unidades,
)
from .views_home import (
    atividades_home_para,
    home,
    montar_atividade_home,
    receita_id_do_log,
    texto_jornal_home,
    url_receita,
    usuarios_da_rede_home_ids,
)
from .views_receitas import (
    cadastrar_receita,
    confirmar_exclusao,
    copiar_receita,
    editar_receita,
    excluir_receita,
    favoritar_receita,
    mostrar_receita,
    mostrar_receitas,
    pesquisar_receitas,
    valida_cadastro_material,
)

__all__ = [
    "atividades_home_para",
    "auditar_mudancas_ingredientes_receita",
    "cadastrar_receita",
    "confirmar_exclusao",
    "copiar_receita",
    "dados_auditoria_ingrediente",
    "dados_auditoria_ingrediente_existente",
    "editar_ingrediente",
    "editar_receita",
    "editar_unidade",
    "excluir_ingrediente",
    "excluir_receita",
    "excluir_unidade",
    "favoritar_receita",
    "gerenciar_ingredientes",
    "gerenciar_unidades",
    "home",
    "montar_atividade_home",
    "mostrar_receita",
    "mostrar_receitas",
    "pesquisar_receitas",
    "receita_id_do_log",
    "texto_jornal_home",
    "url_receita",
    "usuarios_da_rede_home_ids",
    "valida_cadastro_material",
]
