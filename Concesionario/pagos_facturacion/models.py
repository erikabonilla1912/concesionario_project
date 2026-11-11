from djongo import models

# La forma de pago se define una sola vez en la venta (ventas_cotizaciones)
from ventas_cotizaciones.models import Venta


class DetallePago(models.Model):
    TIPOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('cheque', 'Cheque'),
    ]

    tipo_pago = models.CharField(max_length=30, choices=TIPOS_PAGO)
    forma_pago = models.CharField(max_length=20, choices=Venta.FORMAS_PAGO)
    monto = models.FloatField()
    fecha_pago = models.DateField()
    numero_referencia = models.CharField(max_length=50, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        abstract = True


class ItemFactura(models.Model):
    """Concepto cobrado en la factura. El primero siempre es el vehículo vendido."""
    CONCEPTOS = [
        ('vehiculo', 'Vehículo'),
        ('matricula', 'Matrícula y traspaso'),
        ('soat', 'SOAT'),
        ('accesorio', 'Accesorio'),
        ('otro', 'Otro'),
    ]
    concepto = models.CharField(max_length=20, choices=CONCEPTOS)
    descripcion = models.CharField(max_length=150, blank=True)
    cantidad = models.IntegerField(default=1)
    valor_unitario = models.FloatField()

    class Meta:
        abstract = True


class Cuota(models.Model):
    """Cuota del plan de pagos de una factura a crédito."""
    numero = models.IntegerField()
    fecha_vencimiento = models.DateField()
    valor = models.FloatField()

    class Meta:
        abstract = True


class Anulacion(models.Model):
    """Quién anuló la factura, cuándo y por qué."""
    motivo = models.TextField()
    fecha = models.DateTimeField()
    usuario = models.CharField(max_length=150)

    class Meta:
        abstract = True


class Factura(models.Model):
    ESTADOS_FACTURA = [
        ('emitida', 'Emitida'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ]

    numero_factura = models.CharField(max_length=20, unique=True)
    fecha_emision = models.DateField(auto_now_add=True)
    id_cotizacion = models.IntegerField(null=True, blank=True)
    cedula_cliente = models.CharField(max_length=20)
    nombre_cliente = models.CharField(max_length=150)
    placa_vehiculo = models.CharField(max_length=10)
    subtotal = models.FloatField()
    iva_porcentaje = models.FloatField(default=19)
    impuesto_iva = models.FloatField()
    total = models.FloatField()
    estado = models.CharField(max_length=20, choices=ESTADOS_FACTURA, default='emitida')
    items = models.ArrayField(
        model_container=ItemFactura,
        blank=True,
        default=list
    )
    cuotas = models.ArrayField(
        model_container=Cuota,
        blank=True,
        default=list
    )
    pagos = models.ArrayField(
        model_container=DetallePago,
        blank=True
    )
    anulacion = models.EmbeddedField(
        model_container=Anulacion,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'facturas'

    def __str__(self):
        return f"Factura #{self.numero_factura} - {self.nombre_cliente} ({self.estado})"
