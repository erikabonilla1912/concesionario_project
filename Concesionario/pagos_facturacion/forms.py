from django import forms

from Concesionario.formularios import CampoFecha
from clientes_vehiculos.models import Cliente
from ventas_cotizaciones.models import Cotizacion, Venta
from .models import DetallePago, ItemFactura


def opciones_ventas():
    clientes = {c.id: c for c in Cliente.objects.all()}
    opciones = [('', 'Selecciona una venta')]
    for cotizacion in Cotizacion.objects.all().order_by('-id'):
        venta, vehiculo = cotizacion.venta, cotizacion.vehiculo
        cliente = clientes.get(cotizacion.id_cliente)
        if cliente and venta and not venta['numero_factura']:
            texto = (f'{cliente.nombre} {cliente.apellido} · {vehiculo["marca"]} '
                     f'{vehiculo["modelo"]} ({vehiculo["placa"]}) · '
                     f'${venta["precio_final"] or 0:,.0f}').replace(',', '.')
            opciones.append((str(cotizacion.id), texto))
    return opciones


class FormularioFactura(forms.Form):
    venta = forms.ChoiceField(label='Venta a facturar')
    iva_porcentaje = forms.FloatField(label='IVA (%)', min_value=0, max_value=50, initial=19)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['venta'].choices = opciones_ventas()


class FormularioEditarFactura(forms.Form):
    iva_porcentaje = forms.FloatField(label='IVA (%)', min_value=0, max_value=50)

    def __init__(self, *args, subtotal=0, pagado=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtotal = subtotal
        self.pagado = pagado

    def clean(self):
        datos = super().clean()
        iva = datos.get('iva_porcentaje')
        if iva is not None and self.subtotal * (1 + iva / 100) < self.pagado - 0.5:
            raise forms.ValidationError('El nuevo total no puede ser menor a lo que ya se ha pagado.')
        return datos


class FormularioItem(forms.Form):
    concepto = forms.ChoiceField(label='Concepto')
    descripcion = forms.CharField(label='Descripcion', max_length=150, required=False)
    cantidad = forms.IntegerField(label='Cantidad', min_value=1, initial=1)
    valor_unitario = forms.FloatField(label='Valor unitario (COP)', min_value=0)

    def __init__(self, *args, es_vehiculo=False, **kwargs):
        super().__init__(*args, **kwargs)
        if es_vehiculo:
            self.fields['concepto'].choices = [c for c in ItemFactura.CONCEPTOS if c[0] == 'vehiculo']
            self.fields['concepto'].disabled = True
            self.fields['cantidad'].disabled = True
            self.fields['valor_unitario'].help_text = 'Cambiarlo tambien actualiza el precio final de la venta.'
        else:
            self.fields['concepto'].choices = [c for c in ItemFactura.CONCEPTOS if c[0] != 'vehiculo']


class FormularioPlanCuotas(forms.Form):
    numero_cuotas = forms.IntegerField(label='Numero de cuotas', min_value=2, max_value=72, initial=12)
    fecha_primera = CampoFecha(label='Vencimiento de la primera cuota')


class FormularioCuota(forms.Form):
    fecha_vencimiento = CampoFecha(label='Fecha de vencimiento')


class FormularioAnulacion(forms.Form):
    motivo = forms.CharField(label='Motivo de la anulacion', min_length=5, max_length=1000,
                             widget=forms.Textarea(attrs={'rows': 3}))


class FormularioPago(forms.Form):
    tipo_pago = forms.ChoiceField(label='Medio de pago', choices=DetallePago.TIPOS_PAGO)
    forma_pago = forms.ChoiceField(label='Forma', choices=Venta.FORMAS_PAGO)
    monto = forms.FloatField(label='Monto (COP)', min_value=1)
    fecha_pago = CampoFecha(label='Fecha del pago')
    numero_referencia = forms.CharField(label='Numero de referencia', max_length=50, required=False)
    observaciones = forms.CharField(label='Observaciones', required=False,
                                    widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, maximo=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximo = maximo
        self.fields['monto'].help_text = f'Saldo disponible: ${maximo:,.0f}'.replace(',', '.')

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if monto > self.maximo + 0.5:
            raise forms.ValidationError('El pago no puede superar el saldo pendiente.')
        return monto
