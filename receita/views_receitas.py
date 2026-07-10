"""Views do ciclo de vida das receitas."""

from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from autentica import usuario
from logs.utils import registrar_log
from usuarios.models import Grupo

from .auditoria import (
    auditar_mudancas_ingredientes_receita,
    dados_auditoria_ingrediente,
    dados_auditoria_ingrediente_existente,
)
from .models import Ingrediente, Material, Receita, Unidade
from .selectors import receitas_visiveis_para
from .utils import ordenar_objetos_por_nome


@usuario
def cadastrar_receita(request):
    """Exibe o formulario de nova receita com materiais e unidades ordenados."""
    materiais = ordenar_objetos_por_nome(Material.objects.all(), "nome")
    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")

    context = {
        "materiais": materiais,
        "unidades": unidades,
    }
    return render(request, "cadastroReceita.html", context)


@usuario
def valida_cadastro_material(request):
    """Cria receita e ingredientes a partir do formulario serializado da tela."""
    if request.method == "POST":
        nome_receita = request.POST.get("nome")
        modo_preparo = request.POST.get("ModoPreparo")
        ingredientes_string = request.POST.get("IngredientesSelecionados")

        if not nome_receita or not modo_preparo or not ingredientes_string:
            messages.error(request, "Preencha todos os campos da receita.")
            return redirect("cadastrar_receita")

        nova_receita = Receita.objects.create(
            nome=nome_receita,
            modo_de_fazer=modo_preparo,
            usuario=request.user,
            criador_original=request.user,
        )

        registrar_log(
            usuario=request.user,
            acao="CRIAR_RECEITA",
            id_objeto_alvo=nova_receita.id,
            nome_objeto=nova_receita.nome,
        )

        linhas = ingredientes_string.strip().split("\n")

        for linha in linhas:
            if not linha.strip():
                continue

            partes = linha.split(";")
            if len(partes) == 3:
                material_id = int(partes[0])
                quantidade = Decimal(partes[1].replace(",", "."))
                unidade_id = int(partes[2])

                material_obj = Material.objects.get(id=material_id)
                unidade_obj = Unidade.objects.get(id=unidade_id)

                Ingrediente.objects.create(
                    receita=nova_receita,
                    material=material_obj,
                    unidade=unidade_obj,
                    quantidade=quantidade,
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
        return redirect("home")

    return redirect("home")


@usuario
@require_POST
def copiar_receita(request, receita_id):
    """Cria uma copia independente, preservando criador original e data historica."""
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
    """Exibe uma receita somente se ela for propria ou compartilhada por grupo social."""
    try:
        receita_id = int(request.GET.get("receita"))
    except (TypeError, ValueError):
        messages.error(request, "Codigo de receita invalido.")
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
        "ingredientes__unidade",
    ).distinct().first()

    if not receita:
        messages.error(request, "Voce nao tem permissao para visualizar esta receita.")
        return redirect("mostrar_receitas")

    receita.ingredientes_copy = receita.ingredientes.all()
    favoritada = receita.favoritos.filter(id=request.user.id).exists()

    return render(request, "mostrar_receita.html", {
        "receita": receita,
        "favoritada": favoritada,
    })


@usuario
def mostrar_receitas(request):
    """Lista receitas proprias e receitas compartilhadas agrupadas por grupo."""
    usuario_atual = request.user

    receitas_pessoais = list(
        Receita.objects.filter(usuario=usuario_atual).select_related(
            "usuario",
            "criador_original",
        ).order_by("nome")
    )
    receitas_dos_outros = receitas_visiveis_para(usuario_atual).exclude(
        usuario=usuario_atual
    ).select_related(
        "usuario",
        "criador_original",
    ).order_by("nome")
    grupos = Grupo.objects.filter(membros=usuario_atual)

    contador = 1

    for receita in receitas_pessoais:
        receita.numero_exibicao = contador
        contador += 1

    for grupo in grupos:
        grupo.receitas_filtradas = list(
            receitas_dos_outros.filter(usuario__grupos=grupo).distinct()
        )
        for receita in grupo.receitas_filtradas:
            receita.numero_exibicao = contador
            contador += 1

    favoritos_ids = set(
        request.user.receitas_favoritas.values_list("id", flat=True)
    )
    context = {
        "Grupos": grupos,
        "ReceitasPessoais": receitas_pessoais,
        "usuario": usuario_atual.get_full_name(),
        "favoritos_ids": favoritos_ids,
    }

    return render(request, "mostrar_receitas.html", context)


@usuario
def confirmar_exclusao(request):
    """Exibe a confirmacao de exclusao apenas para o dono da receita."""
    try:
        receita_id = int(request.GET.get("receita"))
    except (TypeError, ValueError):
        messages.error(request, "O codigo da receita fornecido e invalido.")
        return redirect("mostrar_receitas")

    try:
        receita = Receita.objects.get(id=receita_id, usuario=request.user)
        return render(request, "confirmar_exclusao.html", {"receita": receita})
    except Receita.DoesNotExist:
        messages.error(request, "Voce nao tem permissao para acessar ou excluir esta receita.")
        return redirect("mostrar_receitas")


@usuario
def excluir_receita(request):
    """Exclui receita propria por POST e remove ingredientes protegidos antes."""
    if request.method == "POST":
        try:
            receita_id = int(request.POST.get("receita_id"))
        except (TypeError, ValueError):
            messages.error(request, "Nao foi possivel processar a exclusao: codigo de receita invalido.")
            return redirect("mostrar_receitas")

        try:
            receita = Receita.objects.get(id=receita_id, usuario=request.user)
            nome_receita = receita.nome

            Ingrediente.objects.filter(receita=receita).delete()

            receita.delete()
            registrar_log(
                usuario=request.user,
                acao="EXCLUIR_RECEITA",
                id_objeto_alvo=receita_id,
                nome_objeto=nome_receita,
            )

            messages.success(request, f"A receita '{nome_receita}' foi excluida permanentemente com sucesso.")
        except Receita.DoesNotExist:
            messages.error(request, "Acao nao autorizada. Voce so pode excluir receitas criadas por voce.")

    return redirect("mostrar_receitas")


@usuario
def editar_receita(request):
    """Atualiza receita propria e registra auditoria das mudancas de ingredientes."""
    try:
        receita_id = int(request.GET.get("receita"))
    except (TypeError, ValueError):
        messages.error(request, "Codigo de receita invalido.")
        return redirect("mostrar_receitas")

    try:
        receita = Receita.objects.get(id=receita_id, usuario=request.user)
    except Receita.DoesNotExist:
        messages.error(request, "Voce nao tem permissao para editar esta receita.")
        return redirect("mostrar_receitas")

    if request.method == "POST":
        nome = request.POST.get("nome")
        modo_preparo = request.POST.get("ModoPreparo")
        ingredientes_string = request.POST.get("IngredientesSelecionados")

        if not nome or not modo_preparo or not ingredientes_string:
            messages.error(request, "Preencha todos os campos da receita.")
            return redirect(f"/receita/editar/?receita={receita.id}")

        ingredientes_anteriores = [
            dados_auditoria_ingrediente_existente(ingrediente)
            for ingrediente in receita.ingredientes.select_related("material", "unidade")
        ]

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

        Ingrediente.objects.filter(receita=receita).delete()
        ingredientes_novos = []

        linhas = ingredientes_string.strip().split("\n")
        for linha in linhas:
            if not linha.strip():
                continue
            partes = linha.split(";")
            if len(partes) == 3:
                material_id = int(partes[0])
                quantidade = Decimal(partes[1].replace(",", "."))
                unidade_id = int(partes[2])

                material_obj = Material.objects.get(id=material_id)
                unidade_obj = Unidade.objects.get(id=unidade_id)

                Ingrediente.objects.create(
                    receita=receita,
                    material=material_obj,
                    unidade=unidade_obj,
                    quantidade=quantidade,
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
        return redirect("mostrar_receitas")

    materiais = ordenar_objetos_por_nome(Material.objects.all(), "nome")
    unidades = ordenar_objetos_por_nome(Unidade.objects.all(), "unidades")

    context = {
        "receita": receita,
        "materiais": materiais,
        "unidades": unidades,
    }
    return render(request, "editar_receita.html", context)


@usuario
def pesquisar_receitas(request):
    """Pesquisa receitas visiveis por nome, autoria original, dono atual ou ingrediente."""
    termo = request.GET.get("q", "").strip()
    receitas = []

    usuario_atual = request.user
    if termo == "":
        receitas = []
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
    """Alterna favorito via POST retornando JSON para a interface."""
    if request.method != "POST":
        return JsonResponse({
            "sucesso": False,
            "erro": "Metodo invalido.",
        }, status=405)

    usuario_atual = request.user

    receita = receitas_visiveis_para(usuario_atual).filter(
        id=receita_id
    ).first()

    if not receita:
        return JsonResponse({
            "sucesso": False,
            "erro": "Receita nao encontrada ou sem permissao.",
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
        "total_favoritos": receita.favoritos.count(),
    })
