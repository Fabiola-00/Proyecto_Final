"""Modelo mínimo de usuario de sesión; los hashes nunca se serializan."""

from flask_login import UserMixin


class Usuario(UserMixin):
    def __init__(self, id, username, nombre, correo, rol, estado, password_version=1, foto_perfil=None):
        self.id = id
        self.username = username
        self.nombre = nombre
        self.correo = correo
        self.rol = rol
        self.estado = estado
        self.password_version = password_version
        self.foto_perfil = foto_perfil

    @property
    def is_active(self):
        return self.estado == "ACTIVO"

    def publico(self):
        return {
            "id": self.id,
            "username": self.username,
            "nombre": self.nombre,
            "rol": self.rol,
            "estado": self.estado,
        }
