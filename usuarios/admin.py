from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(Tipos)
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
   readonly_fields=("nome","email","senha")