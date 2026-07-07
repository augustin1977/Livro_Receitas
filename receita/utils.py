import unicodedata


def normalizar_nome_catalogo(valor):
    if valor is None:
        return ""

    nome = " ".join(str(valor).strip().split())
    return nome.capitalize()


def normalizar_nome_para_comparacao(valor):
    if valor is None:
        return ""

    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return "".join(texto.split())


def nomes_equivalentes(nome_a, nome_b):
    return (
        normalizar_nome_para_comparacao(nome_a) ==
        normalizar_nome_para_comparacao(nome_b)
    )


def existe_nome_equivalente(modelo, campo, nome, pk_ignorado=None):
    consulta = modelo.objects.all()
    if pk_ignorado is not None:
        consulta = consulta.exclude(pk=pk_ignorado)

    return any(
        nomes_equivalentes(getattr(objeto, campo), nome)
        for objeto in consulta
    )
