from typing import Literal, Optional

from pydantic import BaseModel


# CONSULTAR ESTADO DTE
class ConsultarEstadoDTEIn(BaseModel):
    rut_receptor: str
    folio: int
    fecha_dte: str
    monto: int
    tipo_dte: int = 52
    ambiente: int = 0


# ENVIAR SOBRE
class InfoEnvioIn(BaseModel):
    sobres_document_ids: list
    Tipo: int = 1
    Ambiente: int = 0  # 0 ambiente certificacion, 1 ambiente produccion


# GENERAR SOBRE
class Caratula(BaseModel):
    FechaResolucion: str  # Format YYYY-MM-DD
    NumeroResolucion: int = 0
    RutEmisor: Optional[str] = None
    RutReceptor: str = "60803000-K"


class GenerateSobreIn(BaseModel):
    folios: list
    sobre_id: str
    tipo_dte: Literal["GD", "FA"]
    caratula: Caratula
    version: int = 0


# OBTAIN FOLIOS
class ObtainFoliosIn(BaseModel):
    amount: int = 5


# DATOS DTE GD
class IdentificacionDTE(BaseModel):
    TipoDTE: int = 52
    Folio: int
    FechaEmision: str
    TipoTraslado: Optional[
        int
    ]  # 1: constituye venta, 2: venta por efectuar, 3: consignación

    # 4: entrega gratuita, 5: traslados internos,
    # 6: otros traslados no venta, 7: guia de devolucion,
    # 8: traslado exportacion, 9: venta exportacion
    TipoDespacho: int = 2  # 1: por cuenta del receptor,
    # 2 por cuenta del emisor a instalaciones cliente,
    # 3 por cuenta emisor a otras instalaciones
    FormaPago: int = (
        2  # opcional 1: contado, 2: credito, 3: gratis / no se estila ponerlo
    )
    # TpoImpresion: str, no sé cuándo va
    # TpoTranCompra: int, opcional
    # Varios opcionales mas: FmaPagExp, FchCancel, MntCancel, SaldoInsol
    # MntPagos: list, tabla pagos (opcional creo). Si se usa,
    #                               obligatorios: FchPago, MntPago


class Emisor(BaseModel):
    Rut: str
    RazonSocial: str
    Giro: str
    ActividadEconomica: list
    DireccionOrigen: str
    ComunaOrigen: str
    Telefono: Optional[list] = None
    CorreoElectronico: Optional[str] = None


class Receptor(BaseModel):
    Rut: str
    RazonSocial: str
    Giro: str
    Direccion: str
    Comuna: str


class Totales(BaseModel):
    MontoNeto: int
    TasaIVA: int = 19
    IVA: Optional[int] = None
    MontoTotal: int
    MontoExento: Optional[int] = None


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
    Descripcion: Optional[str] = None
    Cantidad: int
    Precio: int
    Descuento: Optional[int] = None
    Recargo: Optional[int] = None
    MontoItem: int


class ReferenciasItem(BaseModel):
    TipoDocumento: int
    FolioReferencia: int
    FechaDocumentoReferencia: str
    CodigoReferencia: Optional[int] = None
    RazonReferencia: str


class Referencias(BaseModel):
    Item: list


class DescuentosRecargos(BaseModel):
    Descripcion: Optional[str] = None
    TipoMovimiento: str
    TipoValor: str
    Valor: float


class Encabezado(BaseModel):
    IdentificacionDTE: IdentificacionDTE
    Emisor: Emisor
    Receptor: Receptor
    Totales: Totales
    Transporte: Optional[Transporte]  # En caso de factura es opcional


class Dte(BaseModel):
    Encabezado: Encabezado
    Detalles: list
    Referencias: Optional[list] = None
    DescuentosRecargos: Optional[list] = None


class GenerateGuiaDespachoIn(BaseModel):
    dte: Dte
    pdf_html_string: str
    version: int = 0
    caf_file_name: str


class GenerateFacturaIn(BaseModel):
    dte: Dte
    # pdf_html_string: str
    datos_extra: Caratula
    caf_file_name: str
    version: int = 0
