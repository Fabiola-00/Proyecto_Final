"""Decoradores reutilizables de autorización en backend."""

from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*roles):
    """Exige sesión válida y al menos uno de los roles indicados."""
    allowed = {role.upper() for role in roles}

    def decorar(view):
        @wraps(view)
        @login_required
        def protegida(*args, **kwargs):
            if current_user.rol not in allowed:
                abort(403)
            return view(*args, **kwargs)

        return protegida

    return decorar
