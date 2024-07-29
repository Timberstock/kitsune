import os
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse

from kitsune_app.middlewares import EmpresaContextMiddleware
from kitsune_app.routers import sii_router
from kitsune_app.setup import firebase_setup


print("Starting firebase setup...")
firebase_setup()
app = FastAPI()
print("Firebase setup correct!")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(exc)
    return PlainTextResponse(str(exc), status_code=400)


@app.get("/")
def root():
    return {"message": "Kitsune Hello World"}


app.include_router(sii_router)

app.add_middleware(EmpresaContextMiddleware)
