from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from usuarios.models import *
from django.db.models import Q
from .models import *
from autentica import *
from django.db.models import Prefetch
from django.contrib import messages 
from decimal import Decimal
from django.db.models.functions import Lower
@usuario_obrigatorio
def cadastrar_receita(request):
    materiais = Material.objects.all().order_by(Lower( 'nome'))
    unidades = Unidade.objects.all().order_by(Lower('unidades'))
    
    context = {
        'materiais': materiais,
        'unidades': unidades
    }
    return render(request, "cadastroReceita.html", context)

def gerenciar_unidades(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_unidade')
        if nome:
            Unidade.objects.create(unidades=nome.capitalize())
        return redirect('gerenciar_unidades')

    unidades = Unidade.objects.all().order_by(Lower('unidades'))
    return render(request, 'gerenciar_unidades.html', {'unidades': unidades})

# View de Edição
def editar_unidade(request, pk):
    try :
        unidade = Unidade.objects.get(pk=pk)
    except:
        messages.error(request, "Unidade não existe")
        redirect("gerenciar_unidades")
    
    if request.method == 'POST':
        nome = request.POST.get('nome_unidade')
        if nome:
            unidade.unidades = nome.capitalize()
            unidade.save()
        return redirect('gerenciar_unidades')
        
    unidades = Unidade.objects.all().order_by(Lower('unidades'))
    return render(request, 'gerenciar_unidades.html', {
        'unidades': unidades,
        'unidade_editando': unidade
    })

# View de Exclusão
def excluir_unidade(request, pk):
    try :
        unidade = Unidade.objects.get(pk=pk)
    except:
        messages.error(request, "Unidade não existe")
        redirect("gerenciar_unidades")
    unidade.delete()
    return redirect('gerenciar_unidades')


@usuario_obrigatorio
def valida_cadastro_material(request):
    if request.method == "POST":
        nome_receita = request.POST.get('nome')
        modo_preparo = request.POST.get('ModoPreparo')
        ingredientes_string = request.POST.get('IngredientesSelecionados')

        if not nome_receita or not modo_preparo or not ingredientes_string:
            messages.error(request, "Preencha todos os campos da receita.")
            return redirect('cadastrar_receita')

        # 1. Cria a Instância da Receita primeiro
        nova_receita = Receita.objects.create(
            nome=nome_receita,
            modo_de_fazer=modo_preparo,
            usuario=request.user # Usuário logado vindo do decorator
        )

        # 2. Processa o texto dos ingredientes
        # Quebra o texto por linhas
        linhas = ingredientes_string.strip().split('\n')
        
        for linha in int(len(linhas)) if isinstance(linhas, str) else linhas:
            if not linha.strip():
                continue
                
            # Cada linha possui: id_material;quantidade;id_unidade
            partes = linha.split(';')
            if len(partes) == 3:
                material_id = int(partes[0])
                quantidade = Decimal(partes[1].replace(',', '.')) # Garante o formato decimal
                unidade_id = int(partes[2])

                # Busca as instâncias do banco
                material_obj = Material.objects.get(id=material_id)
                unidade_obj = Unidade.objects.get(id=unidade_id)

                # Cria o ingrediente vinculado à nova receita
                Ingrediente.objects.create(
                    receita=nova_receita,
                    material=material_obj,
                    unidade=unidade_obj,
                    quantidade=quantidade
                )

        messages.success(request, f"Receita '{nome_receita}' cadastrada com sucesso!")
        return redirect('home')

    return redirect('home')
@usuario_obrigatorio
def mostrar_receita(request):
    # 1. Captura o ID e evita quebras caso o parâmetro venha vazio ou inválido
    try:
        receita_id = int(request.GET.get('receita'))
    except (TypeError, ValueError):
        return redirect('/receita/home/')

    usuario_atual = request.user

    # 2. Tenta buscar a receita aplicando a regra de segurança no próprio banco:
    # O criador deve ser o usuário atual OU a receita deve ser de alguém que compartilha um grupo com ele
    try:
        receita = Receita.objects.get(
            Q(id=receita_id) & (
                Q(usuario=usuario_atual) | 
                Q(usuario__grupos__in=usuario_atual.grupos.all())
            )
        )
    except Receita.DoesNotExist:
        # Se a receita não existir ou o usuário não tiver permissão de acesso,
        # retornamos um erro de Proibido (HTTP 403) ou redirecionamos para a home
        messages.error(request, "Você não tem permissão para visualizar esta receita.")
        return redirect('/receita/home/')

    # 3. Busca os ingredientes vinculados à receita
    # Usamos o 'related_name' que definimos no modelo (ingredientes) para simplificar a busca
    receita.ingredientes_copy = receita.ingredientes.all()

    return render(request, "mostrar_receita.html", {'receita': receita})
@usuario_obrigatorio
def home(request):
    usuario_atual = request.user
    
    # 1. Busca os dados do banco
    receitas_pessoais = list(Receita.objects.filter(usuario=usuario_atual).order_by('nome'))
    receitas_dos_outros = Receita.objects.exclude(usuario=usuario_atual).order_by('nome')
    grupos = Grupo.objects.filter(membros=usuario_atual)
    
    # Inicializa o contador global
    contador = 1
    
    # 2. Numera as receitas pessoais primeiro
    for receita in receitas_pessoais:
        receita.numero_exibicao = contador
        contador += 1
        
    # 3. Numera as receitas de cada grupo sequencialmente
    for grupo in grupos:
        grupo.receitas_filtradas = list(receitas_dos_outros.filter(usuario__grupos=grupo).distinct())
        for receita in grupo.receitas_filtradas:
            receita.numero_exibicao = contador
            contador += 1

    context = {
        'Grupos': grupos,
        'ReceitasPessoais': receitas_pessoais
    }
    
    return render(request, "home.html", context)

@usuario_obrigatorio
def confirmar_exclusao(request):
    try:
        # Tenta capturar o ID da URL
        receita_id = int(request.GET.get('receita'))
    except (TypeError, ValueError):
        # Se o parâmetro 'receita' estiver vazio ou não for um número
        messages.error(request, "O código da receita fornecido é inválido.")
        return redirect('/receita/home/')

    try:
        # Garante que só o dono possa ver a tela de confirmação
        receita = Receita.objects.get(id=receita_id, usuario=request.user)
        return render(request, "confirmar_exclusao.html", {'receita': receita})
    except Receita.DoesNotExist:
        # Se o ID não existir ou se a receita pertencer a outro usuário
        messages.error(request, "Você não tem permissão para acessar ou excluir esta receita.")
        return redirect('/receita/home/')


@usuario_obrigatorio
def excluir_receita(request):
    if request.method == "POST":
        try:
            # Tenta capturar o ID vindo do formulário oculto
            receita_id = int(request.POST.get('receita_id'))
        except (TypeError, ValueError):
            messages.error(request, "Não foi possível processar a exclusão: código de receita inválido.")
            return redirect('/receita/home/')

        try:
            # Trava de segurança no banco de dados
            receita = Receita.objects.get(id=receita_id, usuario=request.user)
            nome_receita = receita.nome

            # 1. Apaga primeiro todos os ingredientes vinculados para liberar o PROTECT
            Ingrediente.objects.filter(receita=receita).delete()

            # 2. Apaga a receita
            receita.delete()

            # Retorno positivo para o usuário
            messages.success(request, f"A receita '{nome_receita}' foi excluída permanentemente com sucesso.")
        except Receita.DoesNotExist:
            messages.error(request, "Ação não autorizada. Você só pode excluir receitas criadas por você.")
        
    return redirect('/receita/home/')

@usuario_obrigatorio
def editar_receita(request):
    try:
        receita_id = int(request.GET.get('receita'))
    except (TypeError, ValueError):
        messages.error(request, "Código de receita inválido.")
        return redirect('/receita/home/')

    try:
        # Garante que apenas o dono possa editar a receita
        receita = Receita.objects.get(id=receita_id, usuario=request.user)
    except Receita.DoesNotExist:
        messages.error(request, "Você não tem permissão para editar esta receita.")
        return redirect('/receita/home/')

    if request.method == "POST":
        nome = request.POST.get('nome')
        modo_preparo = request.POST.get('ModoPreparo')
        ingredientes_string = request.POST.get('IngredientesSelecionados')

        if not nome or not modo_preparo or not ingredientes_string:
            messages.error(request, "Preencha todos os campos da receita.")
            return redirect(f'/receita/editar-receita/?receita={receita.id}')

        # 1. Atualiza os dados principais da receita
        receita.nome = nome
        receita.modo_de_fazer = modo_preparo
        receita.save()

        # 2. Remove os ingredientes antigos para evitar duplicidade ou lixo no banco
        Ingrediente.objects.filter(receita=receita).delete()

        # 3. Insere a nova lista atualizada vinda do formulário
        linhas = ingredientes_string.strip().split('\n')
        for linha in linhas:
            if not linha.strip():
                continue
            partes = linha.split(';')
            if len(partes) == 3:
                material_id = int(partes[0])
                quantidade = Decimal(partes[1].replace(',', '.'))
                unidade_id = int(partes[2])

                Ingrediente.objects.create(
                    receita=receita,
                    material_id=material_id,
                    unidade_id=unidade_id,
                    quantidade=quantidade
                )

        messages.success(request, f"Receita '{nome}' atualizada com sucesso!")
        return redirect('/receita/home/')

    # Se for GET, renderiza a página trazendo as opções de materiais e unidades
    materiais = Material.objects.all().order_by('nome')
    unidades = Unidade.objects.all().order_by('unidades')
    
    context = {
        'receita': receita,
        'materiais': materiais,
        'unidades': unidades,
    }
    return render(request, "editar_receita.html", context)
