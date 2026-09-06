from app import *

# Si tu aplicación Flask se inicializa en app/__init__.py o similar:
try:
    from app import app
except ImportError:
    from app.main import app