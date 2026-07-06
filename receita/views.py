from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from usuarios.models import *
from django.db.models import Q
from django.http import JsonResponse
from .models import *
from autentica import *
from django.db.models import Prefetch
from django.contrib import messages 
from decimal import Decimal
from django.db.models.functions import Lower
from logs.utils import registrar_log

@usuario
def home(request):
    usuario_atual = request.user

    total_receitas_pessoais = Receita.objects.filter(usuario=usuario_atual).count()

    grupos_usuario = Grupo.objects.filter(membros=usuario_atual)
    total_grupos = grupos_usuario.count()

    total_convites = ConviteGrupo.objects.filter(usuario_convidado=usuario_atual).count()

    total_receitas_grupos = Receita.objects.exclude(
        usuario=usuario_atual
    ).filter(
        usuario__grupos__in=grupos_usuario
    ).distinct().count()

    ultimas_receitas = Receita.objects.filter(
        Q(usuario=usuario_atual) |
        Q(usuario__grupos__in=grupos_usuario)
    ).select_related(
        "usuario"
    ).distinct().order_by("-data_cadastro")[:5]

    return render(request, "home.html", {
        "total_receitas_pessoais": total_receitas_pessoais,
        "total_receitas_grupos": total_receitas_grupos,
        "total_grupos": total_grupos,
        "total_convites": total_convites,
        "ultimas_receitas": ultimas_receitas,
    })
    
@usuario
def cadastrar_receita(request):
    materiais = Material.objects.all().order_by(Lower( 'nome'))
    unidades = Unidade.objects.all().order_by(Lower('unidades'))
    
    context = {
        'materiais': materiais,
        'unidades': unidades
    }
    return render(request, "cadastroReceita.html", context)

@admin_geral
def gerenciar_unidades(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_unidade')
        if nome:
            unidade = Unidade(unidades=nome.capitalize())
            unidade.save()
            usuario=request.user
            registrar_log(usuario=usuario,
                    acao='CRIAR_UNIDADE',
                    id_objeto_alvo=unidade.id,
                    nome_objeto=unidade.unidades)
        return redirect('gerenciar_unidades')

    unidades = Unidade.objects.all().order_by(Lower('unidades'))
    return render(request, 'gerenciar_unidades.html', {'unidades': unidades})

@admin_geral
def editar_unidade(request, pk):
    try :
        unidade = Unidade.objects.get(pk=pk)
        nome_antigo= str(unidade.nome)
    except Exception :
        messages.error(request, "Unidade não existe")
        return redirect("gerenciar_unidades")
    
    if request.method == 'POST':
        nome = request.POST.get('nome_unidade')
        if nome:
            unidade.unidades = nome.capitalize()
            unidade.save()
            registrar_log(
                        usuario=request.user, 
                        acao='EDITAR_UNIDADE', 
                        id_objeto_alvo=unidade.id, 
                        nome_objeto=unidade.unidades,
                        dados_anteriores={"nome_anterior":nome_antigo}
                    )
        return redirect('gerenciar_unidades')
        
    unidades = Unidade.objects.all().order_by(Lower('unidades'))
    return render(request, 'gerenciar_unidades.html', {
        'unidades': unidades,
        'unidade_editando': unidade
    })

@admin_geral
def excluir_unidade(request, pk):
    try :
        unidade = Unidade.objects.get(pk=pk)
    except:
        messages.error(request, "Unidade não existe")
        redirect("gerenciar_unidades")
    nome=str(unidade.unidades)
    unidade.delete()
    registrar_log(
                        usuario=request.user, 
                        acao='EXCLUIR_UNIDADE', 
                        id_objeto_alvo=unidade.id,
                        nome_objeto=nome 
                    )
    return redirect('gerenciar_unidades')


@usuario
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
        
        for linha in linhas:
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
@usuario
def mostrar_receita(request):
    try:
        receita_id = int(request.GET.get("receita"))
    except (TypeError, ValueError):
        messages.error(request, "Código de receita inválido.")
        return redirect("mostrar_receitas")

    usuario_atual = request.user

    receita = Receita.objects.filter(
        Q(id=receita_id) & (
            Q(usuario=usuario_atual) |
            Q(usuario__grupos__in=usuario_atual.grupos.all())
        )
    ).select_related(
        "usuario"
    ).prefetch_related(
        "ingredientes",
        "ingredientes__material",
        "ingredientes__unidade"
    ).distinct().first()

    if not receita:
        messages.error(request, "Você não tem permissão para visualizar esta receita.")
        return redirect("mostrar_receitas")

    receita.ingredientes_copy = receita.ingredientes.all()
    favoritada = receita.favoritos.filter(id=request.user.id).exists()

    return render(request, "mostrar_receita.html", {
        "receita": receita,
        "favoritada": favoritada,
    })

    # 3. Busca os ingredientes vinculados à receita
    # Usamos o 'related_name' que definimos no modelo (ingredientes) para simplificar a busca
    receita.ingredientes_copy = receita.ingredientes.all()

    return render(request, "mostrar_receita.html", {'receita': receita})
@usuario
def mostrar_receitas(request):
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
    favoritos_ids = set(
    request.user.receitas_favoritas.values_list("id", flat=True)
)
    context = {
        'Grupos': grupos,
        'ReceitasPessoais': receitas_pessoais,
        'usuario':usuario_atual.get_full_name(),
        "favoritos_ids": favoritos_ids,
    }
    
    return render(request, "mostrar_receitas.html", context)

@usuario
def confirmar_exclusao(request):
    try:
        # Tenta capturar o ID da URL
        receita_id = int(request.GET.get('receita'))
    except (TypeError, ValueError):
        # Se o parâmetro 'receita' estiver vazio ou não for um número
        messages.error(request, "O código da receita fornecido é inválido.")
        return redirect('mostrar_receitas')

    try:
        # Garante que só o dono possa ver a tela de confirmação
        receita = Receita.objects.get(id=receita_id, usuario=request.user)
        return render(request, "confirmar_exclusao.html", {'receita': receita})
    except Receita.DoesNotExist:
        # Se o ID não existir ou se a receita pertencer a outro usuário
        messages.error(request, "Você não tem permissão para acessar ou excluir esta receita.")
        return redirect('mostrar_receitas')


@usuario
def excluir_receita(request):
    if request.method == "POST":
        try:
            # Tenta capturar o ID vindo do formulário oculto
            receita_id = int(request.POST.get('receita_id'))
        except (TypeError, ValueError):
            messages.error(request, "Não foi possível processar a exclusão: código de receita inválido.")
            return redirect('mostrar_receitas')

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
        
    return redirect('mostrar_receitas')

@usuario
def editar_receita(request):
    try:
        receita_id = int(request.GET.get('receita'))
    except (TypeError, ValueError):
        messages.error(request, "Código de receita inválido.")
        return redirect('mostrar_receitas')

    try:
        # Garante que apenas o dono possa editar a receita
        receita = Receita.objects.get(id=receita_id, usuario=request.user)
    except Receita.DoesNotExist:
        messages.error(request, "Você não tem permissão para editar esta receita.")
        return redirect('mostrar_receitas')

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
        return redirect('mostrar_receitas')

    # Se for GET, renderiza a página trazendo as opções de materiais e unidades
    materiais = Material.objects.all().order_by('nome')
    unidades = Unidade.objects.all().order_by('unidades')
    
    context = {
        'receita': receita,
        'materiais': materiais,
        'unidades': unidades,
    }
    return render(request, "editar_receita.html", context)
@admin_geral
def gerenciar_ingredientes(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_ingrediente')
        if nome:
            Material.objects.create(nome=nome.capitalize())
        return redirect('gerenciar_ingredientes')

    ingredientes = Material.objects.all().order_by(Lower('nome'))
    return render(request, 'gerenciar_ingredientes.html', {'ingredientes': ingredientes})

@admin_geral
def editar_ingrediente(request, pk):
    try :
        ingrediente = Material.objects.get(pk=pk)
    except:
        messages.error(request, "Ingrediente não existe")
        return redirect("gerenciar_ingredientes")
    print(ingrediente)  
    if request.method == 'POST':
        nome = request.POST.get('nome_ingrediente')
        if nome:
            ingrediente.nome = nome.capitalize()
            ingrediente.save()
        return redirect('gerenciar_ingredientes')
        
    ingredientes = Material.objects.all().order_by(Lower('nome'))
    return render(request, 'gerenciar_ingredientes.html', {
        'ingredientes': ingredientes,
        'ingrediente_editando': ingrediente
    })

@admin_geral
def excluir_ingrediente(request, pk):
    try :
        ingrediente = Material.objects.get(pk=pk)
    except:
        messages.error(request, "Ingrediente não existe")
        return redirect("gerenciar_ingredientes")
    
    ingrediente.delete()
    return redirect('gerenciar_ingredientes')

def pesquisar_receitas(request):
    termo = request.GET.get("q", "").strip()
    receitas = []


    usuario_atual = request.user
    grupos_usuario = usuario_atual.grupos.all()
    if termo=="":
        receitas=[]
    else:
        receitas = Receita.objects.filter(
            Q(usuario=usuario_atual) |
            Q(usuario__grupos__in=grupos_usuario)
        ).filter(
            Q(nome__icontains=termo) |
            Q(usuario__first_name__icontains=termo) |
            Q(usuario__last_name__icontains=termo) |
            Q(usuario__username__icontains=termo) |
            Q(ingredientes__material__nome__icontains=termo)
        ).select_related(
            "usuario"
        ).distinct().order_by("nome")

    return render(request, "pesquisar_receitas.html", {
        "termo": termo,
        "receitas": receitas,
    })

@usuario
def favoritar_receita(request, receita_id):
    if request.method != "POST":
        return JsonResponse({
            "sucesso": False,
            "erro": "Método inválido."
        }, status=405)

    usuario_atual = request.user

    receita = Receita.objects.filter(
        Q(id=receita_id) & (
            Q(usuario=usuario_atual) |
            Q(usuario__grupos__in=usuario_atual.grupos.all())
        )
    ).distinct().first()

    if not receita:
        return JsonResponse({
            "sucesso": False,
            "erro": "Receita não encontrada ou sem permissão."
        }, status=403)

    if receita.favoritos.filter(id=usuario_atual.id).exists():
        receita.favoritos.remove(usuario_atual)
        favoritada = False
    else:
        receita.favoritos.add(usuario_atual)
        favoritada = True

    return JsonResponse({
        "sucesso": True,
        "favoritada": favoritada,
        "total_favoritos": receita.favoritos.count()
    })