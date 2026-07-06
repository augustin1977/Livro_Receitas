from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib import messages
from receita.models import Receita
from .models import Comentario
from autentica import *
@usuario
def adicionar_comentario(request, receita_id):
    if request.method == "POST":
        try:
            receita = Receita.objects.get(id=receita_id)
        except Receita.DoesNotExist:
            # Se a receita não foi encontrada, envia um aviso amigável
            messages.error(request, "A receita selecionada não foi encontrada ou foi removida.")
            return redirect('lista_receitas')  # Substitua pelo nome correto da sua view de listagem
        texto = request.POST.get("texto")            
        if texto : 
            Comentario.objects.create(
                receita=receita,
                usuario=request.user,
                texto=texto
            )
        # Se tudo deu certo, redireciona para a receita normalmente
        base_url = reverse('mostrar_receita')
        query_string = urlencode({'receita': receita_id})
        return redirect(f"{base_url}?{query_string}")
    return redirect('lista_receitas')
@usuario
def editar_comentario(request, comentario_id):
    if request.method == "POST":
        try:
            comentario = Comentario.objects.get(id=comentario_id)
        except Comentario.DoesNotExist:
            messages.error(request, "O comentário que você tentou editar não existe.")
            return redirect('lista_receitas')
            
        # Garante que um usuário não edite o comentário de outro
        if comentario.usuario != request.user:
            messages.error(request, "Você não tem permissão para editar este comentário.")
            base_url = reverse('mostrar_receita')
            query_string = urlencode({'receita': comentario.receita.id})
            return redirect(f"{base_url}?{query_string}")
            
        novo_texto = request.POST.get("texto")
        if novo_texto:
            comentario.texto = novo_texto
            comentario.save()
            
        base_url = reverse('mostrar_receita')
        query_string = urlencode({'receita': comentario.receita.id})
        return redirect(f"{base_url}?{query_string}")
        
    return redirect('lista_receitas')

@usuario
def excluir_comentario(request, comentario_id):
    try:
        comentario = Comentario.objects.get(id=comentario_id)
    except Comentario.DoesNotExist:
        messages.error(request, "O comentário que você tentou excluir não existe.")
        return redirect('lista_receitas')
        
    # Permite a exclusão se o usuário for o autor do comentário, 
    # o dono da receita associada ou um administrador do sistema
    e_autor_comentario = comentario.usuario == request.user
    e_dono_receita = comentario.receita.usuario == request.user  # Ajuste 'usuario' se o campo da receita tiver outro nome
    e_admin = request.user.is_staff or request.user.is_superuser

    if not (e_autor_comentario or e_dono_receita or e_admin):
        messages.error(request, "Você não tem permissão para excluir este comentário.")
        base_url = reverse('mostrar_receita')
        query_string = urlencode({'receita': comentario.receita.id})
        return redirect(f"{base_url}?{query_string}")
        
    receita_id = comentario.receita.id
    comentario.delete()
    
    messages.success(request, "Comentário removido com sucesso.")
    base_url = reverse('mostrar_receita')
    query_string = urlencode({'receita': receita_id})
    return redirect(f"{base_url}?{query_string}")