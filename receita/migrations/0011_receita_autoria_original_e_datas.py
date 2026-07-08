from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def preencher_dados_historicos(apps, schema_editor):
    Receita = apps.get_model("receita", "Receita")
    for receita in Receita.objects.all().iterator():
        Receita.objects.filter(pk=receita.pk).update(
            criador_original_id=receita.usuario_id,
            data_ultima_modificacao=receita.data_cadastro,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("receita", "0010_material_material_nome_unico_case_insensitive_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="receita",
            name="data_cadastro",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="receita",
            name="criador_original",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receitas_criadas_originalmente",
                to="usuarios.usuario",
            ),
        ),
        migrations.AddField(
            model_name="receita",
            name="data_ultima_modificacao",
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(
            preencher_dados_historicos,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="receita",
            name="criador_original",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receitas_criadas_originalmente",
                to="usuarios.usuario",
            ),
        ),
        migrations.AlterField(
            model_name="receita",
            name="data_ultima_modificacao",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
