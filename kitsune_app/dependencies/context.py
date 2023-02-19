from kitsune_app.middlewares.context import get_empresa_context

def empresa_context() -> dict:
    context = get_empresa_context()
    return context