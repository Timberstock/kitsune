from kitsune_app.middlewares.context import get_empresa_context
from kitsune_app.schemas import EmpresaContext


def empresa_context() -> EmpresaContext:
    """ Dependency function to retrieve the empresa context """
    context = get_empresa_context()
    return context
