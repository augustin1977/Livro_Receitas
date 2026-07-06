from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def popular_dados_sempre(sender, **kwargs):
    # Evita que o script rode multiplas vezes para cada app instalado
    # Substitua 'sua_app_receitas' pelo nome real da sua aplicação
    if sender.name != 'usuarios':
        return

    # Importamos os modelos aqui dentro para evitar problemas de carregamento do Django
    from .models import Tipo

    # 1. Lista de Unidades
    print("Carregando tipos de usuarios básicos.")
    
    tipos_usuarios = ["user","admin_geral","admin_grupo"]
    for tipo in tipos_usuarios:
        # O get_or_create garante que só insere se não existir
        
        _, status = Tipo.objects.get_or_create(tipo=tipo)
        if status:
            print(f"Tipo {tipo} cadastrados com sucesso")
    print("Tipos de usuarios cadastrados com sucesso!")


