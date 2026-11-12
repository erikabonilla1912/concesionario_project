import calendar
import datetime
import unicodedata

from django.db import connection
from django.db.models import Q
from django.shortcuts import redirect, render

from clientes_vehiculos.models import Cliente, Vehiculo
from gestion_usuarios.sesion import registrar_auditoria, requiere_permiso
from ventas_cotizaciones.models import Cotizacion, Venta
from .forms import (FormularioAnulacion, FormularioCuota, FormularioEditarFactura, FormularioFactura,
                    FormularioItem, FormularioPago, FormularioPlanCuotas)
from .models import DetallePago, Factura, ItemFactura


def buscar_factura(id):
    try:
        return Factura.objects.get(id=id)
    except Factura.DoesNotExist:
        return None


def como_fecha(valor):
    return valor.date() if isinstance(valor, datetime.datetime) else valor


def total_pagado(factura):
    return sum(p['monto'] for p in factura.pagos)


def saldo(factura):
    return max(factura.total - total_pagado(factura), 0)


def actualizar_estado(factura):
    if factura.estado != 'anulada':
        factura.estado = 'pagada' if saldo(factura) < 1 else 'emitida'


def porcentaje_iva(factura):
    if factura.iva_porcentaje is not None:
        return factura.iva_porcentaje
    if not factura.subtotal:
        return 0
    return round(factura.impuesto_iva * 100 / factura.subtotal, 2)


def valor_item(item):
    return item['cantidad'] * item['valor_unitario']


def asegurar_items(factura):
    if not factura.items:
        factura.items = [{
            'concepto': 'vehiculo',
            'descripcion': f'Vehiculo {factura.placa_vehiculo}',
            'cantidad': 1,
            'valor_unitario': factura.subtotal,
        }]


def recalcular(factura):
    asegurar_items(factura)
    factura.iva_porcentaje = porcentaje_iva(factura)
    factura.subtotal = sum(valor_item(i) for i in factura.items)
    factura.impuesto_iva = round(factura.subtotal * factura.iva_porcentaje / 100)
    factura.total = factura.subtotal + factura.impuesto_iva
    actualizar_estado(factura)


def siguiente_numero():
    numeros = [int(f.numero_factura.split('-')[1]) for f in Factura.objects.all()]
    connection.ensure_connection()
    esquema = connection.connection['__schema__'].find_one({'name': Factura._meta.db_table}) or {}
    contador = esquema.get('auto', {}).get('seq', 0)
    return f'FAC-{max(numeros + [contador]) + 1:05d}'


def cotizacion_de_factura(factura):
    if factura.id_cotizacion:
        cotizacion = Cotizacion.objects.filter(id=factura.id_cotizacion).first()
        if cotizacion and cotizacion.venta and cotizacion.venta['numero_factura'] == factura.numero_factura:
            return cotizacion
    for cotizacion in Cotizacion.objects.all():
        venta = cotizacion.venta
        if venta and venta['numero_factura'] == factura.numero_factura:
            return cotizacion
    return None


def asignar_numero_a_venta(factura, numero):
    cotizacion = cotizacion_de_factura(factura)
    if cotizacion:
        cotizacion.venta['numero_factura'] = numero
        cotizacion.save()


def sincronizar_venta(factura):
    vehiculo = next((i for i in factura.items if i['concepto'] == 'vehiculo'), None)
    cotizacion = cotizacion_de_factura(factura)
    if vehiculo and cotizacion and cotizacion.venta['precio_final'] != valor_item(vehiculo):
        cotizacion.venta['precio_final'] = valor_item(vehiculo)
        cotizacion.save()


def sumar_meses(fecha, meses):
    mes = fecha.month - 1 + meses
    anio = fecha.year + mes // 12
    mes = mes % 12 + 1
    return datetime.date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def estado_cuotas(factura):
    hoy = datetime.date.today()
    disponible = total_pagado(factura)
    cuotas = []
    for indice, cuota in enumerate(factura.cuotas):
        abonado = min(max(disponible, 0), cuota['valor'])
        disponible -= cuota['valor']
        if abonado >= cuota['valor'] - 0.5:
            estado, texto = 'pagada', 'Pagada'
        elif como_fecha(cuota['fecha_vencimiento']) < hoy:
            estado, texto = 'vencida', 'Vencida'
        elif abonado > 0:
            estado, texto = 'parcial', 'Abonada'
        else:
            estado, texto = 'pendiente', 'Pendiente'
        cuotas.append(dict(cuota, indice=indice, abonado=abonado, estado=estado, texto_estado=texto))
    return cuotas


def nombre_concepto(concepto):
    return dict(ItemFactura.CONCEPTOS).get(concepto, concepto)


def sin_tildes(texto):
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')


def nombre_forma(forma):
    return sin_tildes(dict(Venta.FORMAS_PAGO).get(forma, forma.capitalize()))


def contexto_factura(factura):
    asegurar_items(factura)
    pagado = total_pagado(factura)
    medios = dict(DetallePago.TIPOS_PAGO)
    suma_cuotas = sum(c['valor'] for c in factura.cuotas)
    return {
        'factura': factura,
        'items': [dict(i, indice=n, nombre=nombre_concepto(i['concepto']), valor=valor_item(i))
                  for n, i in enumerate(factura.items)],
        'pagos': [dict(p, indice=n, medio=medios[p['tipo_pago']], forma=nombre_forma(p['forma_pago']))
                  for n, p in enumerate(factura.pagos)],
        'cuotas': estado_cuotas(factura),
        'plan_descuadrado': bool(factura.cuotas) and abs(suma_cuotas - factura.total) > 1,
        'pagado': pagado,
        'saldo': saldo(factura),
        'porcentaje': min(round(pagado * 100 / factura.total), 100) if factura.total else 100,
        'iva_porcentaje': porcentaje_iva(factura),
        'editable': factura.estado != 'anulada',
    }


@requiere_permiso('pagos')
def lista_facturas(request):
    facturas = Factura.objects.all().order_by('-id')
    busqueda = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    if busqueda:
        facturas = facturas.filter(
            Q(numero_factura__icontains=busqueda) | Q(nombre_cliente__icontains=busqueda) |
            Q(cedula_cliente__icontains=busqueda) | Q(placa_vehiculo__icontains=busqueda)
        )
    if estado:
        facturas = facturas.filter(estado=estado)

    filas = [{'factura': f, 'pagado': total_pagado(f), 'saldo': saldo(f)} for f in facturas]
    return render(request, 'pagos_facturacion/lista_facturas.html', {
        'filas': filas,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Factura.ESTADOS_FACTURA,
        'total': Factura.objects.count(),
    })


@requiere_permiso('pagos')
def crear_factura(request):
    if request.method == 'POST':
        formulario = FormularioFactura(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            cotizacion = Cotizacion.objects.get(id=int(datos['venta']))
            cliente = Cliente.objects.get(id=cotizacion.id_cliente)
            vehiculo = cotizacion.vehiculo
            subtotal = cotizacion.venta['precio_final'] or 0
            impuesto = round(subtotal * datos['iva_porcentaje'] / 100)

            factura = Factura.objects.create(
                numero_factura=siguiente_numero(),
                id_cotizacion=cotizacion.id,
                cedula_cliente=cliente.cedula,
                nombre_cliente=f'{cliente.nombre} {cliente.apellido}',
                placa_vehiculo=vehiculo['placa'],
                subtotal=subtotal,
                iva_porcentaje=datos['iva_porcentaje'],
                impuesto_iva=impuesto,
                total=subtotal + impuesto,
                estado='emitida',
                items=[{
                    'concepto': 'vehiculo',
                    'descripcion': f'{vehiculo["marca"]} {vehiculo["modelo"]} {vehiculo["anio"]} · {vehiculo["placa"]}',
                    'cantidad': 1,
                    'valor_unitario': subtotal,
                }],
                cuotas=[],
                pagos=[],
                anulacion=None,
            )
            actualizar_estado(factura)
            if factura.estado != 'emitida':
                factura.save()
            cotizacion.venta['numero_factura'] = factura.numero_factura
            cotizacion.save()
            registrar_auditoria(request, 'crear', 'pagos', f'Genero la factura {factura.numero_factura}')
            return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioFactura(initial={'venta': request.GET.get('venta', '')})

    return render(request, 'pagos_facturacion/formulario_factura.html', {
        'formulario': formulario,
        'titulo': 'Nueva factura',
    })


@requiere_permiso('pagos')
def detalle_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')

    cotizacion = cotizacion_de_factura(factura)
    if cotizacion is None and factura.id_cotizacion:
        cotizacion = Cotizacion.objects.filter(id=factura.id_cotizacion).first()

    contexto = contexto_factura(factura)
    contexto.update({
        'cliente': Cliente.objects.filter(cedula=factura.cedula_cliente).first(),
        'vehiculo': Vehiculo.objects.filter(placa=factura.placa_vehiculo).first(),
        'cotizacion': cotizacion,
        'forma_venta': nombre_forma(cotizacion.venta['forma_pago'])
                       if cotizacion and cotizacion.venta and cotizacion.venta['forma_pago'] else '',
    })
    return render(request, 'pagos_facturacion/detalle_factura.html', contexto)


@requiere_permiso('pagos')
def imprimir_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')
    return render(request, 'pagos_facturacion/factura_imprimible.html', contexto_factura(factura))


@requiere_permiso('pagos')
def editar_factura(request, id):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada':
        return redirect('pagos:lista_facturas')

    asegurar_items(factura)
    subtotal = sum(valor_item(i) for i in factura.items)
    pagado = total_pagado(factura)
    if request.method == 'POST':
        formulario = FormularioEditarFactura(request.POST, subtotal=subtotal, pagado=pagado)
        if formulario.is_valid():
            factura.iva_porcentaje = formulario.cleaned_data['iva_porcentaje']
            recalcular(factura)
            factura.save()
            registrar_auditoria(request, 'editar', 'pagos', f'Edito la factura {factura.numero_factura}')
            return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioEditarFactura(subtotal=subtotal, pagado=pagado, initial={
            'iva_porcentaje': porcentaje_iva(factura),
        })

    return render(request, 'pagos_facturacion/formulario_factura.html', {
        'formulario': formulario,
        'titulo': f'Editar factura {factura.numero_factura}',
        'factura': factura,
    })


@requiere_permiso('pagos')
def anular_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')
    if factura.estado == 'anulada':
        return redirect('pagos:detalle_factura', id=id)

    if request.method == 'POST':
        formulario = FormularioAnulacion(request.POST)
        if formulario.is_valid():
            asignar_numero_a_venta(factura, '')
            factura.estado = 'anulada'
            factura.anulacion = {
                'motivo': formulario.cleaned_data['motivo'],
                'fecha': datetime.datetime.now(),
                'usuario': request.session['usuario']['nombre_usuario'],
            }
            factura.save()
            registrar_auditoria(request, 'editar', 'pagos', f'Anulo la factura {factura.numero_factura}')
            return redirect('pagos:detalle_factura', id=id)
    else:
        formulario = FormularioAnulacion()

    return render(request, 'pagos_facturacion/formulario_anulacion.html', {
        'formulario': formulario,
        'factura': factura,
        'pagado': total_pagado(factura),
    })


@requiere_permiso('pagos')
def eliminar_factura(request, id):
    factura = buscar_factura(id)
    if factura is None:
        return redirect('pagos:lista_facturas')

    con_pagos = bool(factura.pagos)
    if request.method == 'POST' and not con_pagos:
        asignar_numero_a_venta(factura, '')
        factura.delete()
        registrar_auditoria(request, 'eliminar', 'pagos', f'Elimino la factura {factura.numero_factura}')
        return redirect('pagos:lista_facturas')

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar factura',
        'objeto': f'la factura {factura.numero_factura} de {factura.nombre_cliente}',
        'bloqueado': con_pagos,
        'motivo': 'La factura tiene pagos registrados. Puedes anularla en lugar de eliminarla.',
        'advertencia': 'La venta quedara sin factura y se podra volver a facturar.',
        'url_cancelar': 'pagos:detalle_factura',
        'id_cancelar': factura.id,
    })


def guardar_items(request, factura, formulario, accion):
    recalcular(factura)
    if factura.total < total_pagado(factura) - 0.5:
        formulario.add_error(None, 'Con este cambio el total quedaria por debajo de lo que ya se pago.')
        return False
    factura.save()
    sincronizar_venta(factura)
    registrar_auditoria(request, accion, 'pagos', f'Modifico los items de la factura {factura.numero_factura}')
    return True


@requiere_permiso('pagos')
def agregar_item(request, id):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada':
        return redirect('pagos:detalle_factura', id=id)

    asegurar_items(factura)
    if request.method == 'POST':
        formulario = FormularioItem(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            factura.items.append({
                'concepto': datos['concepto'],
                'descripcion': datos['descripcion'],
                'cantidad': datos['cantidad'],
                'valor_unitario': datos['valor_unitario'],
            })
            if guardar_items(request, factura, formulario, 'crear'):
                return redirect('pagos:detalle_factura', id=id)
    else:
        formulario = FormularioItem()

    return render(request, 'pagos_facturacion/formulario_item.html', {
        'formulario': formulario,
        'factura': factura,
        'titulo': 'Agregar item',
    })


@requiere_permiso('pagos')
def editar_item(request, id, indice):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada':
        return redirect('pagos:detalle_factura', id=id)
    asegurar_items(factura)
    if indice >= len(factura.items):
        return redirect('pagos:detalle_factura', id=id)

    item = factura.items[indice]
    es_vehiculo = item['concepto'] == 'vehiculo'
    if request.method == 'POST':
        formulario = FormularioItem(request.POST, es_vehiculo=es_vehiculo, initial={
            'concepto': item['concepto'], 'cantidad': item['cantidad']})
        if formulario.is_valid():
            datos = formulario.cleaned_data
            factura.items[indice] = {
                'concepto': item['concepto'] if es_vehiculo else datos['concepto'],
                'descripcion': datos['descripcion'],
                'cantidad': 1 if es_vehiculo else datos['cantidad'],
                'valor_unitario': datos['valor_unitario'],
            }
            if guardar_items(request, factura, formulario, 'editar'):
                return redirect('pagos:detalle_factura', id=id)
    else:
        formulario = FormularioItem(es_vehiculo=es_vehiculo, initial=item)

    return render(request, 'pagos_facturacion/formulario_item.html', {
        'formulario': formulario,
        'factura': factura,
        'titulo': 'Editar item',
    })


@requiere_permiso('pagos')
def eliminar_item(request, id, indice):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada':
        return redirect('pagos:detalle_factura', id=id)
    asegurar_items(factura)
    if indice >= len(factura.items):
        return redirect('pagos:detalle_factura', id=id)

    item = factura.items[indice]
    nuevo_total = (factura.subtotal - valor_item(item)) * (1 + porcentaje_iva(factura) / 100)
    if item['concepto'] == 'vehiculo':
        bloqueo = 'El item del vehiculo es obligatorio: la factura corresponde a su venta.'
    elif nuevo_total < total_pagado(factura) - 0.5:
        bloqueo = 'Sin este item el total quedaria por debajo de lo que ya se pago.'
    else:
        bloqueo = ''

    if request.method == 'POST' and not bloqueo:
        factura.items.pop(indice)
        recalcular(factura)
        factura.save()
        registrar_auditoria(request, 'eliminar', 'pagos', f'Quito un item de la factura {factura.numero_factura}')
        return redirect('pagos:detalle_factura', id=id)

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Quitar item',
        'objeto': f'{nombre_concepto(item["concepto"])} {item["descripcion"]} de la factura {factura.numero_factura}',
        'bloqueado': bool(bloqueo),
        'motivo': bloqueo,
        'advertencia': 'El subtotal, el IVA y el total se recalculan.',
        'url_cancelar': 'pagos:detalle_factura',
        'id_cancelar': factura.id,
    })


@requiere_permiso('pagos')
def generar_cuotas(request, id):
    factura = buscar_factura(id)
    if factura is None or factura.estado != 'emitida':
        return redirect('pagos:detalle_factura', id=id)

    if request.method == 'POST':
        formulario = FormularioPlanCuotas(request.POST)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            numero = datos['numero_cuotas']
            valor = round(factura.total / numero)
            factura.cuotas = [{
                'numero': n + 1,
                'fecha_vencimiento': sumar_meses(datos['fecha_primera'], n),
                'valor': valor if n < numero - 1 else factura.total - valor * (numero - 1),
            } for n in range(numero)]
            factura.save()
            registrar_auditoria(request, 'crear', 'pagos',
                                f'Genero un plan de {numero} cuotas para la factura {factura.numero_factura}')
            return redirect('pagos:detalle_factura', id=id)
    else:
        formulario = FormularioPlanCuotas(initial={
            'numero_cuotas': len(factura.cuotas) or 12,
            'fecha_primera': sumar_meses(datetime.date.today(), 1),
        })

    return render(request, 'pagos_facturacion/formulario_plan_cuotas.html', {
        'formulario': formulario,
        'factura': factura,
    })


@requiere_permiso('pagos')
def editar_cuota(request, id, indice):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada' or indice >= len(factura.cuotas):
        return redirect('pagos:detalle_factura', id=id)

    cuota = factura.cuotas[indice]
    if request.method == 'POST':
        formulario = FormularioCuota(request.POST)
        if formulario.is_valid():
            cuota['fecha_vencimiento'] = formulario.cleaned_data['fecha_vencimiento']
            factura.save()
            registrar_auditoria(request, 'editar', 'pagos',
                                f'Cambio la fecha de la cuota {cuota["numero"]} de la factura {factura.numero_factura}')
            return redirect('pagos:detalle_factura', id=id)
    else:
        formulario = FormularioCuota(initial={'fecha_vencimiento': como_fecha(cuota['fecha_vencimiento'])})

    return render(request, 'pagos_facturacion/formulario_cuota.html', {
        'formulario': formulario,
        'factura': factura,
        'cuota': cuota,
    })


@requiere_permiso('pagos')
def eliminar_cuotas(request, id):
    factura = buscar_factura(id)
    if factura is None or not factura.cuotas:
        return redirect('pagos:detalle_factura', id=id)

    if request.method == 'POST':
        factura.cuotas = []
        factura.save()
        registrar_auditoria(request, 'eliminar', 'pagos', f'Elimino el plan de cuotas de la factura {factura.numero_factura}')
        return redirect('pagos:detalle_factura', id=id)

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar plan de cuotas',
        'objeto': f'el plan de {len(factura.cuotas)} cuotas de la factura {factura.numero_factura}',
        'advertencia': 'Los pagos ya registrados no se borran.',
        'url_cancelar': 'pagos:detalle_factura',
        'id_cancelar': factura.id,
    })


def datos_pago(datos):
    return {
        'tipo_pago': datos['tipo_pago'],
        'forma_pago': datos['forma_pago'],
        'monto': datos['monto'],
        'fecha_pago': datos['fecha_pago'],
        'numero_referencia': datos['numero_referencia'],
        'observaciones': datos['observaciones'],
    }


def referencia_repetida(factura, referencia, omitir=None):
    return referencia and any(
        i != omitir and p['numero_referencia'] == referencia for i, p in enumerate(factura.pagos))


def forma_sugerida(factura):
    cotizacion = cotizacion_de_factura(factura)
    return cotizacion.venta['forma_pago'] if cotizacion and cotizacion.venta else 'contado'


@requiere_permiso('pagos')
def registrar_pago(request, id):
    factura = buscar_factura(id)
    if factura is None or factura.estado != 'emitida':
        return redirect('pagos:detalle_factura', id=id)

    if request.method == 'POST':
        formulario = FormularioPago(request.POST, maximo=saldo(factura))
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if referencia_repetida(factura, datos['numero_referencia']):
                formulario.add_error('numero_referencia', 'Ya hay un pago con esa referencia en la factura.')
            else:
                factura.pagos.append(datos_pago(datos))
                actualizar_estado(factura)
                factura.save()
                registrar_auditoria(request, 'crear', 'pagos', f'Registro un pago en la factura {factura.numero_factura}')
                return redirect('pagos:detalle_factura', id=factura.id)
    else:
        siguiente = next((c for c in estado_cuotas(factura) if c['estado'] != 'pagada'), None)
        monto = siguiente['valor'] - siguiente['abonado'] if siguiente else saldo(factura)
        formulario = FormularioPago(maximo=saldo(factura), initial={
            'monto': min(monto, saldo(factura)),
            'forma_pago': forma_sugerida(factura),
            'fecha_pago': datetime.date.today(),
        })

    return render(request, 'pagos_facturacion/formulario_pago.html', {
        'formulario': formulario,
        'factura': factura,
        'titulo': 'Registrar pago',
    })


@requiere_permiso('pagos')
def detalle_pago(request, id, indice):
    factura = buscar_factura(id)
    if factura is None or indice >= len(factura.pagos):
        return redirect('pagos:detalle_factura', id=id)

    pago = factura.pagos[indice]
    acumulado = sum(p['monto'] for p in factura.pagos[:indice + 1])
    return render(request, 'pagos_facturacion/detalle_pago.html', {
        'factura': factura,
        'pago': pago,
        'indice': indice,
        'numero': indice + 1,
        'cantidad': len(factura.pagos),
        'medio': dict(DetallePago.TIPOS_PAGO)[pago['tipo_pago']],
        'forma': nombre_forma(pago['forma_pago']),
        'acumulado': acumulado,
        'saldo_despues': max(factura.total - acumulado, 0),
    })


@requiere_permiso('pagos')
def editar_pago(request, id, indice):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada' or indice >= len(factura.pagos):
        return redirect('pagos:detalle_factura', id=id)

    pago = factura.pagos[indice]
    maximo = saldo(factura) + pago['monto']
    if request.method == 'POST':
        formulario = FormularioPago(request.POST, maximo=maximo)
        if formulario.is_valid():
            datos = formulario.cleaned_data
            if referencia_repetida(factura, datos['numero_referencia'], omitir=indice):
                formulario.add_error('numero_referencia', 'Ya hay un pago con esa referencia en la factura.')
            else:
                factura.pagos[indice] = datos_pago(datos)
                actualizar_estado(factura)
                factura.save()
                registrar_auditoria(request, 'editar', 'pagos', f'Edito un pago de la factura {factura.numero_factura}')
                return redirect('pagos:detalle_factura', id=factura.id)
    else:
        formulario = FormularioPago(maximo=maximo, initial=pago)

    return render(request, 'pagos_facturacion/formulario_pago.html', {
        'formulario': formulario,
        'factura': factura,
        'titulo': 'Editar pago',
    })


@requiere_permiso('pagos')
def eliminar_pago(request, id, indice):
    factura = buscar_factura(id)
    if factura is None or factura.estado == 'anulada' or indice >= len(factura.pagos):
        return redirect('pagos:detalle_factura', id=id)

    pago = factura.pagos[indice]
    texto = f'${pago["monto"]:,.0f}'.replace(',', '.')
    if request.method == 'POST':
        factura.pagos.pop(indice)
        actualizar_estado(factura)
        factura.save()
        registrar_auditoria(request, 'eliminar', 'pagos',
                            f'Elimino un pago de {texto} de la factura {factura.numero_factura}')
        return redirect('pagos:detalle_factura', id=id)

    return render(request, 'confirmar_eliminar.html', {
        'titulo': 'Eliminar pago',
        'objeto': f'el pago de {texto} del {como_fecha(pago["fecha_pago"]):%d/%m/%Y} (factura {factura.numero_factura})',
        'advertencia': 'El saldo de la factura aumentara y, si estaba pagada, volvera a quedar emitida.',
        'url_cancelar': 'pagos:detalle_factura',
        'id_cancelar': factura.id,
    })


@requiere_permiso('pagos')
def lista_pagos(request):
    medio = request.GET.get('medio', '')
    medios = dict(DetallePago.TIPOS_PAGO)
    pagos = []
    for factura in Factura.objects.all():
        for indice, pago in enumerate(factura.pagos):
            if not medio or pago['tipo_pago'] == medio:
                pagos.append(dict(pago, factura=factura, indice=indice, medio=medios[pago['tipo_pago']],
                                  forma=nombre_forma(pago['forma_pago']),
                                  anulada=factura.estado == 'anulada'))
    pagos.sort(key=lambda p: p['fecha_pago'], reverse=True)

    return render(request, 'pagos_facturacion/lista_pagos.html', {
        'pagos': pagos,
        'medio': medio,
        'medios': DetallePago.TIPOS_PAGO,
        'total': sum(p['monto'] for p in pagos if not p['anulada']),
        'por_devolver': sum(p['monto'] for p in pagos if p['anulada']),
    })
