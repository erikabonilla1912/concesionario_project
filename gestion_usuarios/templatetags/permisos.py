from django import template

register = template.Library()

@register.filter
def tiene_permiso(user, modulo):
    """
    Uso en template: {{ request.user|tiene_permiso:"clientes" }}
    """
    try:
        return user.perfil.tiene_permiso(modulo)
    except Exception:
        return False

@register.filter
def get_attr(obj, attr):
    """
    Uso en template: {{ rol|get_attr:"perm_clientes" }}
    Usado en form_rol.html para verificar checkboxes.
    """
    return getattr(obj, attr, False)