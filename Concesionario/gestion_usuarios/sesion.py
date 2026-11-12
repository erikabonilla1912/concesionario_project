import datetime
from django.shortcuts import redirect, render
from .models import Usuario

MODULOS = ['clientes', 'historial', 'ventas', 'pagos', 'usuarios']


def iniciar_sesion(request, usuario):
    rol = usuario.rol or {}
    request.session['usuario'] = {
        'id': usuario.id,
        'nombre_usuario': usuario.nombre_usuario,
        'nombre': usuario.nombre,
        'apellido': usuario.apellido,
        'rol': rol.get('nombre', 'Sin rol'),
        'permisos': {modulo: bool(rol.get('perm_' + modulo)) for modulo in MODULOS},
    }


def requiere_permiso(modulo=None):
    def decorador(vista):
        def envoltura(request, *args, **kwargs):
            usuario = request.session.get('usuario')
            if usuario is None:
                return redirect('usuarios:login')
            if modulo and not usuario['permisos'][modulo]:
                return render(request, 'sin_permiso.html', status=403)
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def registrar_auditoria(request, accion, modulo, descripcion, exitoso=True, usuario=None):
    if usuario is None:
        datos = request.session.get('usuario')
        if datos is None:
            return
        usuario = Usuario.objects.filter(id=datos['id']).first()
        if usuario is None:
            return
    usuario.auditoria.append({
        'accion': accion,
        'modulo': modulo,
        'descripcion': descripcion,
        'ip': request.META.get('REMOTE_ADDR', ''),
        'fecha': datetime.datetime.now(),
        'exitoso': exitoso,
    })
    usuario.save()


def vendedor_actual(request):
    datos = request.session['usuario']
    return {
        'nombre_usuario': datos['nombre_usuario'],
        'nombre': datos['nombre'],
        'apellido': datos['apellido'],
    }
