from kitsune_app.middlewares.context import get_empresa_context
from kitsune_app.schemas import EmpresaContext, GenerateGuiaDespachoIn
from kitsune_app.utils import clean_null_terms, document_to_dict


def empresa_context() -> EmpresaContext:
    """Dependency function to retrieve the empresa context"""
    context = get_empresa_context()
    return context


def document_to_guia(generate_dte_params: GenerateGuiaDespachoIn) -> dict:
    """Dependency to set the generate_dte_params as a sendable guia de despacho"""
    guia_despacho = document_to_dict(generate_dte_params.dte)
    guia_despacho = clean_null_terms(guia_despacho)
    return guia_despacho
