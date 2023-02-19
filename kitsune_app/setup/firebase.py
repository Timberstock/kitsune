from contextvars import ContextVar
import firebase_admin
from firebase_admin import firestore


db = ContextVar("Firestore_Database_Client", default=None)

def _initialize_firestore_client():
    _db = firebase_admin.firestore.client()
    db.set(_db)
    
    
def firestore_client() -> firestore.client:
    """
    Returns the firestore database client in the actual context.
    
    Not sure if this is the best approach, maybe using multiple clients for paralelism
    would be better.    
    """
    return db.get()

def firebase_setup():
    """
    Initializes everything regarding firebase setup, function to be called once in main
    """
    firebase_admin.initialize_app()
    _initialize_firestore_client()