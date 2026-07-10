"""Funcoes de auditoria relacionadas aos ingredientes de uma receita."""

from decimal import Decimal

from logs.utils import registrar_log


def dados_auditoria_ingrediente(material, unidade, quantidade):
    """Converte dados de ingrediente para o formato gravado no log."""
    quantidade = Decimal(quantidade)
    return {
        "material_id": material.id,
        "material": material.nome,
        "unidade_id": unidade.id,
        "unidade": unidade.unidades,
        "quantidade": format(quantidade.normalize(), "f"),
    }


def dados_auditoria_ingrediente_existente(ingrediente):
    """Extrai dados de auditoria de um ingrediente ja salvo."""
    return dados_auditoria_ingrediente(
        ingrediente.material,
        ingrediente.unidade,
        ingrediente.quantidade,
    )


def auditar_mudancas_ingredientes_receita(usuario, receita, ingredientes_anteriores, ingredientes_novos):
    """Registra uma linha de log para cada ingrediente incluido, alterado ou removido."""
    anteriores_por_material = {
        ingrediente["material_id"]: ingrediente
        for ingrediente in ingredientes_anteriores
    }
    novos_por_material = {
        ingrediente["material_id"]: ingrediente
        for ingrediente in ingredientes_novos
    }

    for material_id, ingrediente_anterior in anteriores_por_material.items():
        ingrediente_novo = novos_por_material.get(material_id)
        if not ingrediente_novo:
            registrar_log(
                usuario=usuario,
                acao="REMOVER_INGREDIENTE_RECEITA",
                id_objeto_alvo=receita.id,
                nome_objeto=receita.nome,
                dados_anteriores=ingrediente_anterior,
            )
            continue

        if (
            ingrediente_anterior["quantidade"] != ingrediente_novo["quantidade"] or
            ingrediente_anterior["unidade_id"] != ingrediente_novo["unidade_id"]
        ):
            registrar_log(
                usuario=usuario,
                acao="EDITAR_INGREDIENTE_RECEITA",
                id_objeto_alvo=receita.id,
                nome_objeto=receita.nome,
                dados_anteriores=ingrediente_anterior,
                dados_novos=ingrediente_novo,
            )

    for material_id, ingrediente_novo in novos_por_material.items():
        if material_id not in anteriores_por_material:
            registrar_log(
                usuario=usuario,
                acao="ADICIONAR_INGREDIENTE_RECEITA",
                id_objeto_alvo=receita.id,
                nome_objeto=receita.nome,
                dados_novos=ingrediente_novo,
            )
