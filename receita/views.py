from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from usuarios.models import *
from django.db.models import Q
from django.http import JsonResponse
from .models import *
from .selectors import receitas_visiveis_para
from .utils import (
    existe_nome_equivalente,
    normalizar_nome_catalogo,
    ordenar_objetos_por_nome,
)
from autentica import *
from django.db.models import Prefetch
from django.contrib import messages 
from decimal import Decimal
from django.db import transaction
from django.views.decorators.http import require_POST
from logs.models import LogAtividade
from logs.utils import registrar_log


ACOES_JORNAL_HOME = {
    "CRIAR_RECEITA",
    "COPIAR_RECEITA",
    "EDITAR_RECEITA",
    "ADICIONAR_INGREDIENTE_RECEITA",
    "EDITAR_INGREDIENTE_RECEITA",
    "REMOVER_INGREDIENTE_RECEITA",
    "CRIAR_COMENTARIO",
    "EDITAR_COMENTARIO",
    "EXCLUIR_COMENTARIO",
    "FAVORITAR",
    "CRIAR_GRUPO",
    "ENVIAR_CONVITE_GRUPO",
    "ACEITAR_CONVITE_GRUPO",
}

ACOES_RECEITA_HOME = {
    "CRIAR_RECEITA",
    "COPIAR_RECEITA",
    "EDITAR_RECEITA",
    "ADICIONAR_INGREDIENTE_RECEITA",
    "EDITAR_INGREDIENTE_RECEITA",
    "REMOVER_INGREDIENTE_RECEITA",
    "FAVORITAR",
}

ACOES_COMENTARIO_HOME = {
    "CRIAR_COMENTARIO",
    "EDITAR_COMENTARIO",
    "EXCLUIR_COMENTARIO",
}

ACOES_GRUPO_HOME = {
    "CRIAR_GRUPO",
    "ENVIAR_CONVITE_GRUPO",
    "ACEITAR_CONVITE_GRUPO",
}

NOME_GRUPO_TECNICO_SEM_FAMILIA = "Sem_Familia"


def grupos_sociais_do_usuario(usuario):
    return Grupo.objects.filter(membros=usuario).exclude(
        nome=NOME_GRUPO_TECNICO_SEM_FAMILIA
    )


def usuarios_da_rede_home_ids(usuario):
    grupos_usuario = grupos_sociais_do_usuario(usuario)
    usuarios_ids = set(
        Usuario.objects.filter(grupos__in=grupos_usuario).values_list("id", flat=True)
    )
    usuarios_ids.add(usuario.id)
    return usuarios_ids


def url_receita(receita_id):
    return f"{reverse('mostrar_receita')}?receita={receita_id}"


def texto_jornal_home(log, nome):
    usuario = log.usuario.username if log.usuario else "Alguem"

    textos = {
        "CRIAR_RECEITA": f"{usuario} publicou a receita '{nome}'",
        "COPIAR_RECEITA": f"{usuario} copiou a receita '{nome}'",
        "EDITAR_RECEITA": f"{usuario} editou a receita '{nome}'",
        "ADICIONAR_INGREDIENTE_RECEITA": f"{usuario} mexeu nos ingredientes da receita '{nome}'",
        "EDITAR_INGREDIENTE_RECEITA": f"{usuario} mexeu nos ingredientes da receita '{nome}'",
        "REMOVER_INGREDIENTE_RECEITA": f"{usuario} mexeu nos ingredientes da receita '{nome}'",
        "CRIAR_COMENTARIO": f"{usuario} comentou na receita '{nome}'",
        "EDITAR_COMENTARIO": f"{usuario} atualizou um comentario na receita '{nome}'",
        "EXCLUIR_COMENTARIO": f"{usuario} removeu um comentario da receita '{nome}'",
        "FAVORITAR": f"{usuario} favoritou a receita '{nome}'",
        "CRIAR_GRUPO": f"{usuario} criou o grupo '{nome}'",
        "ENVIAR_CONVITE_GRUPO": f"{usuario} movimentou o grupo '{nome}'",
        "ACEITAR_CONVITE_GRUPO": f"{usuario} entrou no grupo '{nome}'",
    }
    return textos.get(log.acao, log.texto_jornal)


def receita_id_do_log(log):
    if log.acao in ACOES_RECEITA_HOME:
        return log.id_objeto_alvo

    if log.acao in ACOES_COMENTARIO_HOME:
        dados = log.dados_novos or log.dados_anteriores or {}
        return dados.get("receita_id")

    return None


def montar_atividade_home(log, receitas_visiveis_ids, grupos_visiveis_ids):
    url = None

    if log.acao in ACOES_RECEITA_HOME or log.acao in ACOES_COMENTARIO_HOME:
        receita_id = receita_id_do_log(log)
        if not receita_id:
            return None

        if receita_id not in receitas_visiveis_ids:
            return None

        receita = Receita.objects.filter(id=receita_id).first()
        if not receita:
            return None

        url = url_receita(receita_id)
        nome = receita.nome

    elif log.acao in ACOES_GRUPO_HOME:
        grupo_id = log.id_objeto_alvo
        if not grupo_id:
            return None

        if grupo_id not in grupos_visiveis_ids:
            return None

        grupo = Grupo.objects.filter(id=grupo_id).first()
        if not grupo:
            return None

        url = reverse("gerenciar_grupo", args=[grupo_id])
        nome = grupo.nome
    else:
        return None

    return {
        "texto": texto_jornal_home(log, nome),
        "url": url,
        "data": log.data,
        "acao": log.acao,
    }


def atividades_home_para(usuario, limite=5):
    usuarios_rede_ids = usuarios_da_rede_home_ids(usuario)
    receitas_visiveis_ids = set(
        receitas_visiveis_para(usuario).values_list("id", flat=True)
    )
    grupos_visiveis_ids = set(
        grupos_sociais_do_usuario(usuario).values_list("id", flat=True)
    )

    atividades = []
    logs = LogAtividade.objects.select_related("usuario").filter(
        acao__in=ACOES_JORNAL_HOME,
        usuario_id__in=usuarios_rede_ids,
    )[:50]

    for log in logs:
        atividade = montar_atividade_home(
            log,
            receitas_visiveis_ids,
            grupos_visiveis_ids,
        )
        if atividade:
            atividades.append(atividade)

        if len(atividades) == limite:
            break

    return atividades


def dados_auditoria_ingrediente(material, unidade, quantidade):
    quantidade = Decimal(quantidade)
    return {
        "material_id": material.id,
        "material": material.nome,
        "unidade_id": unidade.id,
        "unidade": unidade.unidades,
        "quantidade": format(quantidade.normalize(), "f"),
    }


def dados_auditoria_ingrediente_existente(ingrediente):
    return dados_auditoria_ingrediente(
        ingrediente.material,
        ingrediente.unidade,
        ingrediente.quantidade,
    )


def auditar_mudancas_ingredientes_receita(usuario, receita, ingredientes_anteriores, ingredientes_novos):
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


@usuario
def home(request):
    usuario_atual = request.user

    total_receitas_pessoais = Receita.objects.filter(usuario=usuario_atual).count()

    grupos_usuario = Grupo.objects.filter(membros=usuario_atual)
    total_grupos = grupos_usuario.count()

    total_convites = ConviteGrupo.objects.filter(usuario_convidado=usuario_atual).count()

    total_receitas_grupos = receitas_visiveis_para(usuario_atual).exclude(
        usuario=usuario_atual
    ).count()

    ultimas_receitas = receitas_visiveis_para(usuario_atual).select_related(
        "usuario",
        "criador_original",
    ).order_by("-data_ultima_modificacao")[:5]

    atividades_jornal = atividades_home_para(usuario_atual)

    return render(request, "home.html", {
        "total_receitas_pessoais": total_receitas_pessoais,
        "total_receitas_grupos": total_receitas_grupos,
        "total_grupos": total_grupos,
        "total_convites": total_convites,
        "ultimas_receitas": ultimas_receitas,
        "atividades_jornal": atividades_jornal,
    })
    
@usuario
def cadastrar_receita(request):
    materiais = ordenar_objetos_por_nome(Material.objects.all(), "nome")
    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")
    
    context = {
        'materiais': materiais,
        'unidades': unidades
    }
    return render(request, "cadastroReceita.html", context)

@admin_geral
def gerenciar_unidades(request):
    if request.method == 'POST':
        nome = normalizar_nome_catalogo(request.POST.get('nome_unidade'))
        if nome:
            if existe_nome_equivalente(Unidade, "unidades", nome):
                messages.error(request, "Esta unidade ja esta cadastrada.")
                return redirect('gerenciar_unidades')

            unidade = Unidade(unidades=nome)
            unidade.save()
            usuario=request.user
            registrar_log(usuario=usuario,
                    acao='CRIAR_UNIDADE',
                    id_objeto_alvo=unidade.id,
                    nome_objeto=unidade.unidades)
        return redirect('gerenciar_unidades')

    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")
    return render(request, 'gerenciar_unidades.html', {'unidades': unidades})

@admin_geral
def editar_unidade(request, pk):
    try :
        unidade = Unidade.objects.get(pk=pk)
        nome_antigo = str(unidade.unidades)
    except Exception :
        messages.error(request, "Unidade não existe")
        return redirect("gerenciar_unidades")
    
    if request.method == 'POST':
        nome = normalizar_nome_catalogo(request.POST.get('nome_unidade'))
        if nome:
            if existe_nome_equivalente(
                Unidade,
                "unidades",
                nome,
                pk_ignorado=unidade.pk,
            ):
                messages.error(request, "Esta unidade ja esta cadastrada.")
                return redirect('gerenciar_unidades')

            unidade.unidades = nome
            unidade.save()
            registrar_log(
                        usuario=request.user, 
                        acao='EDITAR_UNIDADE', 
                        id_objeto_alvo=unidade.id, 
                        nome_objeto=unidade.unidades,
                        dados_anteriores={"nome_anterior":nome_antigo}
                    )
        return redirect('gerenciar_unidades')
        
    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")
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
        return redirect("gerenciar_unidades")
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
            usuario=request.user, # Usuário logado vindo do decorator
            criador_original=request.user,
        )

        registrar_log(
            usuario=request.user,
            acao="CRIAR_RECEITA",
            id_objeto_alvo=nova_receita.id,
            nome_objeto=nova_receita.nome,
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
                registrar_log(
                    usuario=request.user,
                    acao="ADICIONAR_INGREDIENTE_RECEITA",
                    id_objeto_alvo=nova_receita.id,
                    nome_objeto=nova_receita.nome,
                    dados_novos=dados_auditoria_ingrediente(
                        material_obj,
                        unidade_obj,
                        quantidade,
                    ),
                )

        messages.success(request, f"Receita '{nome_receita}' cadastrada com sucesso!")
        return redirect('home')

    return redirect('home')


@usuario
@require_POST
def copiar_receita(request, receita_id):
    receita_original = receitas_visiveis_para(request.user).filter(
        id=receita_id
    ).select_related(
        "usuario",
        "criador_original",
    ).prefetch_related(
        "ingredientes",
    ).first()

    if not receita_original:
        messages.error(request, "Voce nao tem permissao para copiar esta receita.")
        return redirect("mostrar_receitas")

    if receita_original.usuario_id == request.user.id:
        messages.error(request, "Esta receita ja pertence a voce.")
        return redirect("mostrar_receitas")

    with transaction.atomic():
        nova_receita = Receita.objects.create(
            nome=receita_original.nome,
            modo_de_fazer=receita_original.modo_de_fazer,
            data_cadastro=receita_original.data_cadastro,
            usuario=request.user,
            criador_original=receita_original.criador_original,
        )
        Ingrediente.objects.bulk_create([
            Ingrediente(
                receita=nova_receita,
                material=ingrediente.material,
                unidade=ingrediente.unidade,
                quantidade=ingrediente.quantidade,
            )
            for ingrediente in receita_original.ingredientes.all()
        ])
        registrar_log(
            usuario=request.user,
            acao="COPIAR_RECEITA",
            id_objeto_alvo=nova_receita.id,
            nome_objeto=nova_receita.nome,
            dados_novos={
                "receita_origem_id": receita_original.id,
                "criador_original_id": receita_original.criador_original_id,
            },
        )

    messages.success(
        request,
        f"A receita '{nova_receita.nome}' foi copiada para as suas receitas.",
    )
    return redirect(f"{reverse('mostrar_receita')}?receita={nova_receita.id}")


@usuario
def mostrar_receita(request):
    try:
        receita_id = int(request.GET.get("receita"))
    except (TypeError, ValueError):
        messages.error(request, "Código de receita inválido.")
        return redirect("mostrar_receitas")

    usuario_atual = request.user

    receita = receitas_visiveis_para(usuario_atual).filter(
        id=receita_id
    ).select_related(
        "usuario",
        "criador_original",
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
    receitas_pessoais = list(
        Receita.objects.filter(usuario=usuario_atual).select_related(
            "usuario",
            "criador_original"
        ).order_by("nome")
    )
    receitas_dos_outros = receitas_visiveis_para(usuario_atual).exclude(
        usuario=usuario_atual
    ).select_related(
        "usuario",
        "criador_original"
    ).order_by("nome")
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
            registrar_log(
                usuario=request.user,
                acao="EXCLUIR_RECEITA",
                id_objeto_alvo=receita_id,
                nome_objeto=nome_receita,
            )

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
            return redirect(f'/receita/editar/?receita={receita.id}')

        ingredientes_anteriores = [
            dados_auditoria_ingrediente_existente(ingrediente)
            for ingrediente in receita.ingredientes.select_related("material", "unidade")
        ]

        # 1. Atualiza os dados principais da receita
        dados_anteriores = {
            "nome": receita.nome,
            "modo_de_fazer": receita.modo_de_fazer,
        }
        receita.nome = nome
        receita.modo_de_fazer = modo_preparo
        receita.save()
        registrar_log(
            usuario=request.user,
            acao="EDITAR_RECEITA",
            id_objeto_alvo=receita.id,
            nome_objeto=receita.nome,
            dados_anteriores=dados_anteriores,
            dados_novos={
                "nome": nome,
                "modo_de_fazer": modo_preparo,
            },
        )

        # 2. Remove os ingredientes antigos para evitar duplicidade ou lixo no banco
        Ingrediente.objects.filter(receita=receita).delete()
        ingredientes_novos = []

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

                material_obj = Material.objects.get(id=material_id)
                unidade_obj = Unidade.objects.get(id=unidade_id)

                Ingrediente.objects.create(
                    receita=receita,
                    material=material_obj,
                    unidade=unidade_obj,
                    quantidade=quantidade
                )
                ingredientes_novos.append(
                    dados_auditoria_ingrediente(
                        material_obj,
                        unidade_obj,
                        quantidade,
                    )
                )

        auditar_mudancas_ingredientes_receita(
            request.user,
            receita,
            ingredientes_anteriores,
            ingredientes_novos,
        )

        messages.success(request, f"Receita '{nome}' atualizada com sucesso!")
        return redirect('mostrar_receitas')

    # Se for GET, renderiza a página trazendo as opções de materiais e unidades
    materiais = ordenar_objetos_por_nome(Material.objects.all(), "nome")
    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")
    
    context = {
        'receita': receita,
        'materiais': materiais,
        'unidades': unidades,
    }
    return render(request, "editar_receita.html", context)
@admin_geral
def gerenciar_ingredientes(request):
    if request.method == 'POST':
        nome = normalizar_nome_catalogo(request.POST.get('nome_ingrediente'))
        if nome:
            if existe_nome_equivalente(Material, "nome", nome):
                messages.error(request, "Este ingrediente ja esta cadastrado.")
                return redirect('gerenciar_ingredientes')

            material = Material.objects.create(nome=nome)
            registrar_log(
                usuario=request.user,
                acao="CRIAR_MATERIAL",
                id_objeto_alvo=material.id,
                nome_objeto=material.nome,
            )
        return redirect('gerenciar_ingredientes')

    ingredientes = ordenar_objetos_por_nome(Material.objects.all(), "nome")
    return render(request, 'gerenciar_ingredientes.html', {'ingredientes': ingredientes})

@admin_geral
def editar_ingrediente(request, pk):
    try :
        ingrediente = Material.objects.get(pk=pk)
    except:
        messages.error(request, "Ingrediente não existe")
        return redirect("gerenciar_ingredientes")
    if request.method == 'POST':
        nome = normalizar_nome_catalogo(request.POST.get('nome_ingrediente'))
        if nome:
            if existe_nome_equivalente(
                Material,
                "nome",
                nome,
                pk_ignorado=ingrediente.pk,
            ):
                messages.error(request, "Este ingrediente ja esta cadastrado.")
                return redirect('gerenciar_ingredientes')

            nome_antigo = ingrediente.nome
            ingrediente.nome = nome
            ingrediente.save()
            registrar_log(
                usuario=request.user,
                acao="EDITAR_MATERIAL",
                id_objeto_alvo=ingrediente.id,
                nome_objeto=ingrediente.nome,
                dados_anteriores={"nome": nome_antigo},
            )
        return redirect('gerenciar_ingredientes')
        
    ingredientes = ordenar_objetos_por_nome(Material.objects.all(), "nome")
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
    
    nome = ingrediente.nome
    ingrediente_id = ingrediente.id
    ingrediente.delete()
    registrar_log(
        usuario=request.user,
        acao="EXCLUIR_MATERIAL",
        id_objeto_alvo=ingrediente_id,
        nome_objeto=nome,
    )
    return redirect('gerenciar_ingredientes')
@usuario
def pesquisar_receitas(request):
    termo = request.GET.get("q", "").strip()
    receitas = []


    usuario_atual = request.user
    if termo=="":
        receitas=[]
    else:
        receitas = receitas_visiveis_para(usuario_atual).filter(
            Q(nome__icontains=termo) |
            Q(usuario__first_name__icontains=termo) |
            Q(usuario__last_name__icontains=termo) |
            Q(usuario__username__icontains=termo) |
            Q(criador_original__first_name__icontains=termo) |
            Q(criador_original__last_name__icontains=termo) |
            Q(criador_original__username__icontains=termo) |
            Q(ingredientes__material__nome__icontains=termo)
        ).select_related(
            "usuario",
            "criador_original",
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

    receita = receitas_visiveis_para(usuario_atual).filter(
        id=receita_id
    ).first()

    if not receita:
        return JsonResponse({
            "sucesso": False,
            "erro": "Receita não encontrada ou sem permissão."
        }, status=403)

    if receita.favoritos.filter(id=usuario_atual.id).exists():
        receita.favoritos.remove(usuario_atual)
        favoritada = False
        registrar_log(
            usuario=usuario_atual,
            acao="DESFAVORITAR",
            id_objeto_alvo=receita.id,
            nome_objeto=receita.nome,
        )
    else:
        receita.favoritos.add(usuario_atual)
        favoritada = True
        registrar_log(
            usuario=usuario_atual,
            acao="FAVORITAR",
            id_objeto_alvo=receita.id,
            nome_objeto=receita.nome,
        )

    return JsonResponse({
        "sucesso": True,
        "favoritada": favoritada,
        "total_favoritos": receita.favoritos.count()
    })
