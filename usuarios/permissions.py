"""Regras de permissao compartilhadas pelas views de grupos."""


def usuario_e_admin_geral(request):
    return request.user.is_staff or request.user.is_superuser


def usuario_administra_grupo(request, grupo):
    """Centraliza quem pode executar acoes administrativas em um grupo."""
    return usuario_e_admin_geral(request) or grupo.administradores.filter(
        id=request.user.id
    ).exists()
