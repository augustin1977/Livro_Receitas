from django.contrib import admin
from .models import *
# Register your models here.



# @admin.register(Usuario)
# class UsuarioAdmin(admin.ModelAdmin):
#    readonly_fields=("nome","email","senha")
admin.site.register(Tipo)
admin.site.register(Grupo)
admin.site.register(Usuario)