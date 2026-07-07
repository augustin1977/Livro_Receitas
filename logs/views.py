from django.shortcuts import render

from autentica import admin_geral

from .models import LogAtividade


@admin_geral
def painel_administrador_logs(request):
    acao_filtro = request.GET.get("acao")
    if acao_filtro:
        logs = LogAtividade.objects.filter(acao=acao_filtro)
    else:
        logs = LogAtividade.objects.all()

    return render(request, "painel_logs.html", {"logs": logs})
