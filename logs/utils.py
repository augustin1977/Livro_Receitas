from .models import LogAtividade
from autentica import *



def registrar_log(usuario, acao, id_objeto_alvo=None, nome_objeto=None, dados_anteriores=None):
    if usuario:
        log_temp = LogAtividade(acao=acao)
        display_acao = log_temp.get_acao_display()
        
        # Monta a base do texto: "NomeUsuario fez tal ação"
        texto_jornal = f"{usuario.username} {display_acao.lower()}"
        
        # Se você passou o nome do objeto (uma receita ou grupo), complementa a frase
        if nome_objeto:
            texto_jornal = f"{texto_jornal}: '{nome_objeto}'"
            
        LogAtividade.objects.create(
            usuario=usuario,
            acao=acao,
            texto_jornal=texto_jornal,
            id_objeto_alvo=id_objeto_alvo,
            dados_anteriores=dados_anteriores
        )