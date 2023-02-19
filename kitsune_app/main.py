import firebase_admin  # type: ignore

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse

from .routers import sii_router
from .middlewares import EmpresaContextMiddleware

from .setup import firebase_setup

firebase_setup()
app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)


@app.get("/")
def root():
    return {"message": "Kitsune Hello World"}


app.include_router(sii_router)

app.add_middleware(EmpresaContextMiddleware)
