import os

from dotenv import load_dotenv

import base64


def auth_to_base64(key):
    """Convert the API key into a base64 string"""

    SimpleAPI_KEY = key
    SimpleAPI_KEY = ("api:" + SimpleAPI_KEY).encode("ascii")
    SimpleAPI_KEY = base64.b64encode(SimpleAPI_KEY)
    base64_message = SimpleAPI_KEY.decode("ascii")
    auth_64_message = "Basic " + base64_message
    return auth_64_message


load_dotenv()

FIREBASE_BUCKET = os.getenv("FIREBASE_BUCKET")
SIMPLEAPI_KEY = os.getenv("SIMPLEAPI_KEY")

AUTH = auth_to_base64(SIMPLEAPI_KEY)


# Security pls xd
SALT = os.getenv("SALT")
