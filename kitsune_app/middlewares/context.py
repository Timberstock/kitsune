# TODO: Add middlewares for the FIREBASE authentication for buckets, the certificate
# authentication for the SII, and the API key authentication for the SimpleAPI header.

from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

from kitsune_app.schemas import EmpresaContext
from kitsune_app.settings import SALT
from kitsune_app.utils import get_certificate_credentials


# CONTEXT LOGIC
EMPRESA_CTX_KEY = "empresa_context"

_empresa_ctx_var: ContextVar[EmpresaContext] = ContextVar(
    EMPRESA_CTX_KEY, default=EmpresaContext()
)


def get_empresa_context() -> EmpresaContext:
    return _empresa_ctx_var.get()


# MIDDLEWARE
class EmpresaContextMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        context_model = EmpresaContext()

        # actual state of endpoints always have rut_empresa as the second path param
        empresa_id_value = scope["path"].split("/")[2]
        pfx_certificate_value = get_certificate_credentials(empresa_id_value, SALT)

        context_model.empresa_id = empresa_id_value
        context_model.pfx_certificate = pfx_certificate_value
        empresa_context = _empresa_ctx_var.set(context_model)

        await self.app(scope, receive, send)

        _empresa_ctx_var.reset(empresa_context)
