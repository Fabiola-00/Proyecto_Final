"""Almacenamiento privado y validación básica de fotos de perfil PNG/JPEG."""

import binascii
import struct
import uuid
from pathlib import Path

from flask import current_app

MAX_BYTES = 3 * 1024 * 1024
MAX_DIMENSION = 4096


def _validar_png(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset, visto_header, visto_datos = 8, False, False
    while offset + 12 <= len(data):
        longitud = struct.unpack(">I", data[offset:offset + 4])[0]
        tipo = data[offset + 4:offset + 8]
        final = offset + 12 + longitud
        if final > len(data):
            return False
        contenido = data[offset + 8:offset + 8 + longitud]
        crc = struct.unpack(">I", data[offset + 8 + longitud:final])[0]
        if binascii.crc32(tipo + contenido) & 0xffffffff != crc:
            return False
        if not visto_header:
            if tipo != b"IHDR" or longitud != 13:
                return False
            ancho, alto = struct.unpack(">II", contenido[:8])
            if not (1 <= ancho <= MAX_DIMENSION and 1 <= alto <= MAX_DIMENSION):
                return False
            visto_header = True
        elif tipo == b"IDAT":
            visto_datos = True
        elif tipo == b"IEND":
            return longitud == 0 and visto_datos and final == len(data)
        offset = final
    return False


def _validar_jpeg(data):
    if len(data) < 16 or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        return False
    offset, dimension = 2, False
    while offset < len(data) - 2:
        if data[offset] != 0xff:
            return False
        while offset < len(data) and data[offset] == 0xff:
            offset += 1
        if offset >= len(data):
            return False
        marker = data[offset]
        offset += 1
        if marker in (0xd8, 0xd9) or 0xd0 <= marker <= 0xd7 or marker == 0x01:
            if marker == 0xd9:
                break
            continue
        if offset + 2 > len(data):
            return False
        longitud = struct.unpack(">H", data[offset:offset + 2])[0]
        if longitud < 2 or offset + longitud > len(data):
            return False
        if marker in {0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf}:
            if longitud < 7:
                return False
            alto, ancho = struct.unpack(">HH", data[offset + 3:offset + 7])
            if not (1 <= ancho <= MAX_DIMENSION and 1 <= alto <= MAX_DIMENSION):
                return False
            dimension = True
        offset += longitud
        if marker == 0xda:
            break
    return dimension


def guardar_foto(archivo):
    if archivo is None:
        return None
    data = archivo.stream.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValueError("La imagen debe pesar como máximo 3 MiB.")
    if _validar_png(data):
        extension = ".png"
    elif _validar_jpeg(data):
        extension = ".jpg"
    else:
        raise ValueError("Usa una imagen PNG o JPEG válida de hasta 4096 × 4096 píxeles.")
    nombre = f"{uuid.uuid4().hex}{extension}"
    carpeta = Path(current_app.config["PERFIL_MEDIA_FOLDER"])
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_bytes(data)
    return nombre
