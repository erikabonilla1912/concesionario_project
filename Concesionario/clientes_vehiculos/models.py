from djongo import models


class PropietarioAnterior(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        abstract = True


class Mantenimiento(models.Model):
    TIPOS = [
        ('cambio_aceite', 'Cambio de aceite'),
        ('frenos', 'Revision de frenos'),
        ('llantas', 'Cambio de llantas'),
        ('revision_general', 'Revision general'),
        ('otro', 'Otro'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPOS)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField()
    costo = models.FloatField(null=True, blank=True)

    class Meta:
        abstract = True


class Vehiculo(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('vendido', 'Vendido'),
    ]
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    color = models.CharField(max_length=30, blank=True)
    placa = models.CharField(max_length=10)
    precio = models.FloatField(null=True, blank=True)
    kilometraje = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    descripcion = models.TextField(blank=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateField(auto_now=True)
    propietarios_anteriores = models.ArrayField(
        model_container=PropietarioAnterior,
        blank=True
    )
    mantenimientos = models.ArrayField(
        model_container=Mantenimiento,
        blank=True
    )

    class Meta:
        db_table = 'vehiculos'

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.anio})"


class VehiculoCotizacion(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    placa = models.CharField(max_length=10)
    precio = models.FloatField(null=True, blank=True)

    class Meta:
        abstract = True


class DetalleVendedor(models.Model):
    nombre_usuario = models.CharField(max_length=150)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    class Meta:
        abstract = True


class Pago(models.Model):
    TIPOS = [('contado', 'Contado'), ('cuota', 'Cuota')]
    tipo = models.CharField(max_length=10, choices=TIPOS)
    monto = models.FloatField(null=True, blank=True)
    fecha = models.DateField()
    numero_cuota = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True


class Factura(models.Model):
    numero_factura = models.CharField(max_length=20)
    fecha_emision = models.DateField()
    subtotal = models.FloatField(null=True, blank=True)
    impuesto = models.FloatField(null=True, blank=True)
    total = models.FloatField(null=True, blank=True)
    pagos = models.ArrayField(model_container=Pago, blank=True)

    class Meta:
        abstract = True


class Venta(models.Model):
    fecha_venta = models.DateField(null=True, blank=True)
    precio_final = models.FloatField(null=True, blank=True)
    forma_pago = models.CharField(max_length=50, blank=True)
    factura = models.EmbeddedField(
        model_container=Factura,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class Cotizacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    vehiculo = models.EmbeddedField(model_container=VehiculoCotizacion)
    vendedor = models.EmbeddedField(model_container=DetalleVendedor)
    precio_ofertado = models.FloatField(null=True, blank=True)
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    notas = models.TextField(blank=True)
    venta = models.EmbeddedField(
        model_container=Venta,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField(blank=True)
    fecha_registro = models.DateField(auto_now_add=True)
    cotizaciones = models.ArrayField(
        model_container=Cotizacion,
        blank=True
    )

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"