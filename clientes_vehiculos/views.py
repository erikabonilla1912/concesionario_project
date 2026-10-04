from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from gestion_usuarios.decorators import requiere_permiso
from .models import Cliente, Vehiculo

@requiere_permiso('clientes')
def lista_clientes(request):
    q = request.GET.get('q','')
    clientes = Cliente.objects.filter(nombre__icontains=q) | Cliente.objects.filter(cedula__icontains=q) if q else Cliente.objects.all()
    return render(request, 'clientes_vehiculos/lista_clientes.html', {'clientes': clientes, 'q': q})

@requiere_permiso('clientes')
def nuevo_cliente(request):
    if request.method == 'POST':
        try:
            Cliente.objects.create(
                nombre=request.POST['nombre'], apellido=request.POST['apellido'],
                cedula=request.POST['cedula'], email=request.POST.get('email',''),
                telefono=request.POST['telefono'], direccion=request.POST.get('direccion','')
            )
            messages.success(request, 'Cliente registrado exitosamente.')
            return redirect('lista_clientes')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'clientes_vehiculos/form_cliente.html', {'accion': 'Nuevo'})

@requiere_permiso('clientes')
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.nombre = request.POST['nombre']; cliente.apellido = request.POST['apellido']
        cliente.cedula = request.POST['cedula']; cliente.email = request.POST.get('email','')
        cliente.telefono = request.POST['telefono']; cliente.direccion = request.POST.get('direccion','')
        cliente.save(); messages.success(request, 'Cliente actualizado.')
        return redirect('lista_clientes')
    return render(request, 'clientes_vehiculos/form_cliente.html', {'cliente': cliente, 'accion': 'Editar'})

@requiere_permiso('clientes')
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete(); messages.success(request, 'Cliente eliminado.')
        return redirect('lista_clientes')
    return render(request, 'clientes_vehiculos/confirmar_eliminar.html', {'objeto': cliente, 'tipo': 'cliente'})

@requiere_permiso('clientes')
def lista_vehiculos(request):
    estado = request.GET.get('estado','')
    vehiculos = Vehiculo.objects.filter(estado=estado) if estado else Vehiculo.objects.all()
    return render(request, 'clientes_vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos, 'estado': estado})

@requiere_permiso('clientes')
def nuevo_vehiculo(request):
    if request.method == 'POST':
        try:
            Vehiculo.objects.create(
                marca=request.POST['marca'], modelo=request.POST['modelo'],
                anio=request.POST['anio'], color=request.POST['color'],
                placa=request.POST['placa'], precio=request.POST['precio'],
                kilometraje=request.POST.get('kilometraje',0),
                estado=request.POST.get('estado','disponible'),
                descripcion=request.POST.get('descripcion','')
            )
            messages.success(request, 'Vehículo registrado.')
            return redirect('lista_vehiculos')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'clientes_vehiculos/form_vehiculo.html', {'accion': 'Nuevo'})

@requiere_permiso('clientes')
def editar_vehiculo(request, pk):
    v = get_object_or_404(Vehiculo, pk=pk)
    if request.method == 'POST':
        v.marca=request.POST['marca']; v.modelo=request.POST['modelo']; v.anio=request.POST['anio']
        v.color=request.POST['color']; v.placa=request.POST['placa']; v.precio=request.POST['precio']
        v.kilometraje=request.POST.get('kilometraje',0); v.estado=request.POST.get('estado','disponible')
        v.descripcion=request.POST.get('descripcion',''); v.save()
        messages.success(request, 'Vehículo actualizado.')
        return redirect('lista_vehiculos')
    return render(request, 'clientes_vehiculos/form_vehiculo.html', {'vehiculo': v, 'accion': 'Editar'})

@requiere_permiso('clientes')
def eliminar_vehiculo(request, pk):
    v = get_object_or_404(Vehiculo, pk=pk)
    if request.method == 'POST':
        v.delete(); messages.success(request, 'Vehículo eliminado.')
        return redirect('lista_vehiculos')
    return render(request, 'clientes_vehiculos/confirmar_eliminar.html', {'objeto': v, 'tipo': 'vehículo'})