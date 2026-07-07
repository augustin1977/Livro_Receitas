from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def popular_dados_sempre(sender, **kwargs):
    # Evita que o script rode multiplas vezes para cada app instalado
    # Substitua 'sua_app_receitas' pelo nome real da sua aplicação
    if sender.name != 'receita':
        return

    # Importamos os modelos aqui dentro para evitar problemas de carregamento do Django
    from .models import Unidade, Material
    from .utils import existe_nome_equivalente, normalizar_nome_catalogo

    # 1. Lista de Unidades
    print("Carregando unidades basicas de culinária.")
    unidades_dados = [
        'Grama',
        'Quilograma',
        'Mililitro',
        'Litro',
        'Unidade',
        'Xícara de chá',
        'Colher de sopa',
        'Colher de chá',
        'Colher de café',
        'Pitada',
        'a Gosto',
        "Copo",
        "Lata",
    ]

    for unidades in unidades_dados:
        # O get_or_create garante que só insere se não existir
        unidades = normalizar_nome_catalogo(unidades)
        status = False
        if not existe_nome_equivalente(Unidade, "unidades", unidades):
            Unidade.objects.create(unidades=unidades)
            status = True
        if status:
            print (f"unidade {unidades} Criada com sucesso")
    print ("Unidades de medida cadastrados com sucesso!")
    # 2. Lista de Materiais
    print("Carregando ingredientes basicos.")
    materiais_dados = [
        'Açúcar Refinado',
        'Farinha de Trigo',
        'Sal',
        'Leite Integral',
        'Óleo de Soja',
        'Ovo',
        'Manteiga',
        'Fermento em Pó',
        'Água',
        'Fermento Biológico',
        'Creme de Leite',
        'Leite Condensado',
        'Açucar Cristal',
        'Mel',
        'Leite em Pó',
        "Chocolate em Pó",
        "Achocolatado",
        "Milho de Pipoca",
        "Fubá",
        "Farinha de mandicoa",
        "Creme de leite fresco",
        "Queijo Minas Padrão",
        "Polvilho Doce",
        "Polvilho Azedo",
        "Mostarda",
        "Picanha",
        "Alcatra",
        "Contra Filé",
        "Maionese",
        "Batata Inglesa",
        "Batata Doce",
        "Goiabada",
        "Açucar de confeiteiro",       
    ]

    for nome in materiais_dados:
        nome = normalizar_nome_catalogo(nome)
        status = False
        if not existe_nome_equivalente(Material, "nome", nome):
            Material.objects.create(nome=nome)
            status = True
        if status:
            print (f"Ingrediente {nome} cadastrado com com sucesso")
    print ("Ingedientes cadastrados com sucesso")
