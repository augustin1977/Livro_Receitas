from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import Group  # Se usar o modelo de grupos padrão do Django
# Se você tiver um modelo próprio de grupo (ex: Grupo), importe de receita.models ou usuarios.models
from receita.models import Receita
from social.models import Comentario
from usuarios.models import Usuario
from .models import LogAtividade
from autentica import *


@admin_geral
def painel_administrador_logs(request):        
    acao_filtro = request.GET.get('acao')
    if acao_filtro:
        logs = LogAtividade.objects.filter(acao=acao_filtro)
    else:
        logs = LogAtividade.objects.all()
        
    return render(request, 'painel_logs.html', {'logs': logs})

@admin_geral
def desfazer_acao_log(request, log_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Permissão negada.")
        return redirect('lista_receitas')
        
    try:
        log = LogAtividade.objects.get(id=log_id)
    except LogAtividade.DoesNotExist:
        messages.error(request, "Log de atividade não encontrado.")
        return redirect('painel_administrador_logs')
        
    if log.foi_desfeito:
        messages.warning(request, "Esta ação já foi revertida anteriormente.")
        return redirect('painel_administrador_logs')

    try:
        # 1. Interações Sociais
        if log.acao == 'COMENTAR':
            Comentario.objects.filter(id=log.id_objeto_alvo).delete()
            
        # 2. Ações de Receitas
        elif log.acao == 'CRIAR_RECEITA':
            Receita.objects.filter(id=log.id_objeto_alvo).delete()
            
        elif log.acao in ['EXCLUIR_RECEITA', 'EDITAR_RECEITA', 'COPIAR_RECEITA']:
            messages.warning(request, "Ações de exclusão, edição ou cópia de receitas devem ser verificadas manualmente no banco de dados.")
            return redirect('painel_administrador_logs')

        # 3. Ações de Grupos
        elif log.acao == 'CRIAR_GRUPO':
            # Remove o grupo criado pelo ID salvo
            Group.objects.filter(id=log.id_objeto_alvo).delete()
            
        elif log.acao == 'ADICIONAR_MEMBRO':
            # Para remover o membro, precisamos ler os dados que guardamos no log (ID do grupo e ID do usuário)
            # Supondo que id_objeto_alvo seja o ID do grupo e guardamos o ID do usuário em dados_anteriores
            if log.dados_anteriores and 'usuario_id' in log.dados_anteriores:
                grupo = Group.objects.get(id=log.id_objeto_alvo)
                membro = Usuario.objects.get(id=log.dados_anteriores['usuario_id'])
                grupo.user_set.remove(membro) # Remove o usuário do grupo
                
        elif log.acao == 'REMOVER_MEMBRO':
            # Devolve o membro ao grupo
            if log.dados_anteriores and 'usuario_id' in log.dados_anteriores:
                grupo = Group.objects.get(id=log.id_objeto_alvo)
                membro = Usuario.objects.get(id=log.dados_anteriores['usuario_id'])
                grupo.user_set.add(membro)

        # 4. Ações de Segurança e Conta (Não faz sentido deletar o usuário ou reverter login/logout por um botão)
        elif log.acao in ['CADASTRAR_USUARIO', 'LOGIN', 'LOGOUT', 'ALTERAR_SENHA', 'DESFAZER_ACAO']:
            messages.warning(request, "Este tipo de ação informativa não pode ser desfeita pelo painel.")
            return redirect('painel_administrador_logs')

        # Se passou pelas checagens e executou a reversão, finaliza o processo
        log.foi_desfeito = True
        log.save()
        
        # Registra a moderação realizada pelo administrador para auditoria
        from .utils import registrar_log
        
        # Registra a moderação usando o seu padrão ideal
        texto_reversao = f"O administrador {request.user.username} desfez a ação: '{log.texto_jornal}'"
        
        registrar_log(
            usuario=request.user,
            acao='DESFAZER_ACAO',
            texto_jornal=texto_reversao,
            id_objeto_alvo=log.id
        )

        messages.success(request, "Ação revertida com sucesso!")
    except Exception:
        messages.error(request, "Não foi possível reverter a ação automaticamente. O registro original pode ter sido modificado ou excluído por outro usuário.")
        
    return redirect('painel_administrador_logs')