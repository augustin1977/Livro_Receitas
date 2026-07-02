from .models import *

def contador_convites(request):
    if request.user.is_authenticated:
        total = ConviteGrupo.objects.filter(usuario_convidado=request.user).count()
        return {'total_convites': total}
    return {'total_convites': 0}
