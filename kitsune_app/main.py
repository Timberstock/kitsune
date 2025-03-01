from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from kitsune_app.middlewares import EmpresaContextMiddleware
from kitsune_app.routers import sii_router
from kitsune_app.setup import firebase_setup


print("Starting firebase setup...")
firebase_setup()
app = FastAPI(debug=True)
print("Firebase setup correct!")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the request, the body and the headers
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )
    print("[ERROR] Request Validation Error")
    print("Response content:", response.body.decode())  # Print decoded response body
    print("Status code:", response.status_code)
    print("Validation errors:", exc.errors())

    # https://fastapi.tiangolo.com/tutorial/handling-errors/#override-the-httpexception-error-handler
    return response


@app.get("/")
def root():
    return {"message": "Kitsune Hello World"}


app.include_router(sii_router)

app.add_middleware(EmpresaContextMiddleware)
