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

    # 1. Lista de Unidades
    print("Carregando unidades basicas de culinária.")
    unidades_dados = [
        ('g', 'Grama'),
        ('kg', 'Quilograma'),
        ('ml', 'Mililitro'),
        ('l', 'Litro'),
        ('un', 'Unidade'),
        ('xic. chá', 'Xícara de Chá'),
        ('c. sopa', 'Colher de Sopa'),
        ('c. chá', 'Colher de Chá'),
        ('c. café', 'Colher de Café'),
        ('pitada','Pitada'),
        ('a gosto','a Gosto'),
    ]

    unidades_objetos = {}
    for simbolo, nome in unidades_dados:
        # O get_or_create garante que só insere se não existir
        unidade_obj, _ = Unidade.objects.get_or_create(simbolo=simbolo, defaults={'unidades': nome})
        unidades_objetos[simbolo] = unidade_obj
        print (f"unidade  {nome} : {simbolo} Criada com sucesso")
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
        'Creme de Leite'
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
        "Mel",
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
        Material.objects.get_or_create(nome=nome)
        print (f"Ingrediente {nome} cadastrado com com sucesso")
    print ("Ingedientes cadastrados com sucesso")