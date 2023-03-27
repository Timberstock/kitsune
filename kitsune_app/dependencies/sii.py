from kitsune_app.middlewares.context import get_empresa_context
from kitsune_app.utils import clean_null_terms, document_to_dict
from kitsune_app.schemas import EmpresaContext, GuiaDespachoDocumentoIn


def empresa_context() -> EmpresaContext:
    """Dependency function to retrieve the empresa context"""
    context = get_empresa_context()
    return context


def document_to_guia(document: GuiaDespachoDocumentoIn) -> dict:
    """Dependency to set the document as a sendable guia de despacho"""
    guia_despacho = document_to_dict(document)
    guia_despacho = clean_null_terms(guia_despacho)
    return guia_despacho