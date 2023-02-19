import os

from dotenv import load_dotenv

from kitsune_app.utils.auth import auth_to_base64


load_dotenv()

FIREBASE_BUCKET = os.getenv("FIREBASE_BUCKET")
SIMPLEAPI_KEY = os.getenv("SIMPLEAPI_KEY")

AUTH = auth_to_base64(SIMPLEAPI_KEY)


# Security pls xd
SALT = os.getenv("SALT")
