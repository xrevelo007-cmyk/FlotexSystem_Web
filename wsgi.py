import sys
import os

# Agrega la ruta actual al sistema para asegurar que reconozca los módulos
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import *

# Si tu archivo principal dentro de app expone la variable app:
try:
    from app.app import app
except ImportError:
    try:
        from app.main import app
    except ImportError:
        pass