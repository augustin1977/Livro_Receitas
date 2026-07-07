from django.shortcuts import render
from django.db.models import Q
from autentica import admin_geral
from .models import LogAtividade



@admin_geral
def painel_administrador_logs(request):
    acao_filtro = request.GET.get("acao")
    if acao_filtro=="RECEITA":
        filtro=(Q(acao="CRIAR_RECEITA")|
                Q(acao="EDITAR_RECEITA")|        
                Q(acao="EXCLUIR_RECEITA")|
                Q(acao="ADICIONAR_INGREDIENTE_RECEITA")|
                Q(acao="EDITAR_INGREDIENTE_RECEITA")|
                Q(acao="REMOVER_INGREDIENTE_RECEITA"))
        logs = LogAtividade.objects.filter(filtro)
    elif acao_filtro=="COMENTARIO":
        filtro=(Q(acao="CRIAR_COMENTARIO")|
                Q(acao="EDITAR_COMENTARIO")|
                Q(acao="EXCLUIR_COMENTARIO"))
        logs = LogAtividade.objects.filter(filtro)
    elif acao_filtro=="GRUPO":
        filtro=(Q(acao="CRIAR_GRUPO")|
                Q(acao="EXCLUIR_GRUPO")|
                Q(acao="ENVIAR_CONVITE_GRUPO")|
                Q(acao="ACEITAR_CONVITE_GRUPO")|
                Q(acao="RECUSAR_CONVITE_GRUPO")|
                Q(acao="SAIR_GRUPO")|
                Q(acao="REMOVER_MEMBRO")|
                Q(acao="PROMOVER_ADMIN_GRUPO")|
                Q(acao="REVOGAR_ADMIN_GRUPO"))
        logs = LogAtividade.objects.filter(filtro)
    elif acao_filtro=="USUARIO":
        filtro=(Q(acao="CADASTRAR_USUARIO")|
                Q(acao="EDITAR_USUARIO")|
                Q(acao="EXCLUIR_USUARIO"))
        logs = LogAtividade.objects.filter(filtro)
    elif acao_filtro=="FAVORITOS":
        filtro=(Q(acao="FAVORITAR")|
                Q(acao="DESFAVORITAR"))
        logs = LogAtividade.objects.filter(filtro)
    else:
        acao_filtro = None
        logs = LogAtividade.objects.all()

    return render(request, "painel_logs.html", {
        "logs": logs,
        "acao_filtro": acao_filtro,
    })
