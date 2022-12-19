from pydantic import BaseModel

# ENVIAR SOBRE
class InfoEnvio(BaseModel):
    Tipo: int = 1
    Ambiente: int = 0


# GENERAR SOBRE
class SobreCaratula(BaseModel):
    RutEmisor: str = None
    RutReceptor: str = "60803000-K"
    FechaResolucion: str
    NumeroResolucion: int = 0


# OBTAIN FOLIOS
class ObtainFolios(BaseModel):
    amount: int = 5


# DATOS DTE GD
class IdentificacionDTE(BaseModel):
    TipoDTE: int = 52
    Folio: int
    FechaEmision: str
    TipoTraslado: int = 1  # 1: constituye venta, 2: venta por efectuar, 3: consignación, 4: entrega gratuita, 5: traslados internos, 6: otros traslados no venta, 7: guia de devolucion, 8: traslado exportacion, 9: venta exportacion
    TipoDespacho: int = 2  # 1: por cuenta del receptor, 2 por cuenta del emisor a instalaciones cliente, 3 por cuenta emisor a otras instalaciones
    FormaPago: int = 2  # opcional 1: contado, 2: credito, 3: gratis
    # TpoImpresion: str, no sé cuándo va
    # TpoTranCompra: int, opcional
    # Varios opcionales mas: FmaPagExp, FchCancel, MntCancel, SaldoInsol
    # MntPagos: list, tabla pagos (opcional creo). Si se usa, obligatorios: FchPago, MntPago


class Emisor(BaseModel):
    Rut: str
    RazonSocial: str
    Giro: str
    ActividadEconomica: list
    DireccionOrigen: str
    ComunaOrigen: str
    Telefono: list = None
    CorreoElectronico: str = None


class Receptor(BaseModel):
    Rut: str
    RazonSocial: str
    Giro: str
    Direccion: str
    Comuna: str


class Totales(BaseModel):
    MontoNeto: int
    MontoExento: int = None
    TasaIVA: int = 19
    Iva: int = None
    MontoTotal: int


class Chofer(BaseModel):
    Rut: str
    Nombre: str


class Transporte(BaseModel):
    Patente: str
    RutTransportista: str
    DireccionDestino: str
    ComunaDestino: str
    CiudadDestino: str
    Chofer: Chofer


class DetalleItem(BaseModel):
    IndicadorExento: int
    Nombre: str
    Descripcion: str = None
    Cantidad: int
    Precio: int
    Descuento: int = None
    Recargo: int = None
    MontoItem: int


class ReferenciasItem(BaseModel):
    TipoDocumento: int
    FolioReferencia: int
    FechaDocumentoReferencia: str
    CodigoReferencia: int = None
    RazonReferencia: str


class Referencias(BaseModel):
    Item: list


class DescuentosRecargos(BaseModel):
    Descripcion: str = None
    TipoMovimiento: str
    TipoValor: str
    Valor: float


class Encabezado(BaseModel):
    IdentificacionDTE: IdentificacionDTE
    Emisor: Emisor
    Receptor: Receptor
    Totales: Totales
    Transporte: Transporte


class GuiaDespachoDocumento(BaseModel):
    Encabezado: Encabezado
    Detalles: list
    Referencias: list = None
    DescuentosRecargos: list = None
