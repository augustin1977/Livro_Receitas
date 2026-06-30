from django.apps import AppConfig


class ReceitaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "receita"
    def ready(self):
        # Importa os sinais para garantir que o Django os registre no início
        import receita.signals