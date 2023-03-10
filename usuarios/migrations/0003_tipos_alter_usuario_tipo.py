# Generated by Django 4.1 on 2023-01-16 19:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0002_usuario_tipo"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tipos",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tipo", models.CharField(max_length=20)),
            ],
        ),
        migrations.AlterField(
            model_name="usuario",
            name="tipo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="usuarios.tipos"
            ),
        ),
    ]
