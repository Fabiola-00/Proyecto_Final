"""Extensiones Flask desacopladas de la fábrica de aplicación."""

from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
csrf = CSRFProtect()
