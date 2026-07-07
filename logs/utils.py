from .models import LogAtividade


ROTULOS_CAMPOS = {
    "nome": "nome",
    "modo_de_fazer": "modo de preparo",
    "texto": "comentario",
}


def _valor_legivel(valor):
    if valor is None:
        return ""
    return str(valor).replace("\r\n", "\n").replace("\r", "\n").strip()


def _mudancas_legiveis(dados_anteriores, dados_novos):
    if not dados_anteriores or not dados_novos:
        return ""

    partes = []
    for campo, valor_antigo in dados_anteriores.items():
        if campo not in dados_novos:
            continue

        valor_novo = dados_novos[campo]
        if valor_antigo == valor_novo:
            continue

        rotulo = ROTULOS_CAMPOS.get(campo, campo.replace("_", " "))
        partes.append(
            f"{rotulo} mudou de '{_valor_legivel(valor_antigo)}' "
            f"para '{_valor_legivel(valor_novo)}'"
        )

    return "; ".join(partes)


def _descricao_ingrediente(dados):
    if not dados:
        return ""

    quantidade = _valor_legivel(dados.get("quantidade"))
    unidade = _valor_legivel(dados.get("unidade"))
    material = _valor_legivel(dados.get("material"))
    return f"{quantidade} {unidade} de {material}".strip()


def _montar_texto_jornal(
    usuario,
    acao,
    display_acao,
    nome_objeto=None,
    dados_anteriores=None,
    dados_novos=None,
):
    if acao == "CRIAR_COMENTARIO":
        texto = _valor_legivel((dados_novos or {}).get("texto"))
        return (
            f"{usuario.username} criou o comentario na receita "
            f"'{nome_objeto}': '{texto}'"
        )

    if acao == "EDITAR_COMENTARIO":
        mudancas = _mudancas_legiveis(dados_anteriores, dados_novos)
        return (
            f"{usuario.username} editou o comentario da receita "
            f"'{nome_objeto}': {mudancas}"
        )

    if acao == "EXCLUIR_COMENTARIO":
        texto = _valor_legivel((dados_anteriores or {}).get("texto"))
        return (
            f"{usuario.username} excluiu o comentario da receita "
            f"'{nome_objeto}': '{texto}'"
        )

    if acao == "EDITAR_RECEITA":
        mudancas = _mudancas_legiveis(dados_anteriores, dados_novos)
        return (
            f"{usuario.username} editou a receita "
            f"'{nome_objeto}': {mudancas}"
        )

    if acao == "ADICIONAR_INGREDIENTE_RECEITA":
        ingrediente = _descricao_ingrediente(dados_novos)
        return (
            f"{usuario.username} adicionou ingrediente na receita "
            f"'{nome_objeto}': '{ingrediente}'"
        )

    if acao == "REMOVER_INGREDIENTE_RECEITA":
        ingrediente = _descricao_ingrediente(dados_anteriores)
        return (
            f"{usuario.username} removeu ingrediente da receita "
            f"'{nome_objeto}': '{ingrediente}'"
        )

    if acao == "EDITAR_INGREDIENTE_RECEITA":
        ingrediente_antigo = _descricao_ingrediente(dados_anteriores)
        ingrediente_novo = _descricao_ingrediente(dados_novos)
        material = _valor_legivel(
            (dados_novos or {}).get("material") or
            (dados_anteriores or {}).get("material")
        )
        return (
            f"{usuario.username} editou ingrediente da receita "
            f"'{nome_objeto}': '{material}' mudou de "
            f"'{ingrediente_antigo}' para '{ingrediente_novo}'"
        )

    texto_jornal = f"{usuario.username} {display_acao.lower()}"
    if nome_objeto:
        texto_jornal = f"{texto_jornal}: '{nome_objeto}'"
    return texto_jornal


def registrar_log(
    usuario,
    acao,
    id_objeto_alvo=None,
    nome_objeto=None,
    dados_anteriores=None,
    dados_novos=None,
):
    if not usuario:
        return

    log_temp = LogAtividade(acao=acao)
    display_acao = log_temp.get_acao_display()
    texto_jornal = _montar_texto_jornal(
        usuario=usuario,
        acao=acao,
        display_acao=display_acao,
        nome_objeto=nome_objeto,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
    )

    LogAtividade.objects.create(
        usuario=usuario,
        acao=acao,
        texto_jornal=texto_jornal,
        id_objeto_alvo=id_objeto_alvo,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
    )
