"""Residencia e incorporación del perfil, sin inferir datos históricos."""
from datetime import date

DEPARTAMENTOS_BOLIVIA = (
    "Beni", "Chuquisaca", "Cochabamba", "La Paz", "Oruro",
    "Pando", "Potosí", "Santa Cruz", "Tarija",
)
PAISES_RESIDENCIA = ("Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica", "Cuba", "Ecuador", "El Salvador", "Guatemala", "Haití", "Honduras", "México", "Nicaragua", "Panamá", "Paraguay", "Perú", "República Dominicana", "Uruguay", "Venezuela")
CAMPOS_RESIDENCIA = {"pais_residencia", "departamento_residencia", "ano_incorporacion", "nacionalidad", "fecha_incorporacion"}

def leer_geografia(conexion, usuario_id):
    fila = conexion.execute("SELECT pais_residencia, departamento_residencia, nacionalidad FROM perfil_geografico WHERE voluntario_id=?", (usuario_id,)).fetchone()
    return dict(fila) if fila else {}

def guardar_geografia(conexion, usuario_id, valores, anteriores=None):
    if not {"pais_residencia", "departamento_residencia", "nacionalidad"}.intersection(valores): return
    perfil = dict(anteriores or {}); perfil.update(valores)
    conexion.execute("""INSERT INTO perfil_geografico(voluntario_id,pais_residencia,departamento_residencia,nacionalidad)
       VALUES (?,?,?,?) ON CONFLICT(voluntario_id) DO UPDATE SET pais_residencia=excluded.pais_residencia,
       departamento_residencia=excluded.departamento_residencia,nacionalidad=excluded.nacionalidad""",
       (usuario_id,perfil.get("pais_residencia"),perfil.get("departamento_residencia"),perfil.get("nacionalidad")))


def validar_perfil_residencia(datos, existentes=None, hoy=None):
    existentes = existentes or {}
    hoy = hoy or date.today()
    cambios = {}
    if {"pais_residencia", "departamento_residencia"}.intersection(datos):
        for campo in ("pais_residencia", "departamento_residencia"):
            valor = datos.get(campo, existentes.get(campo))
            if valor is not None and not isinstance(valor, str):
                raise ValueError("La residencia no es válida.")
            cambios[campo] = valor.strip() or None if valor is not None else None
        pais, departamento = cambios["pais_residencia"], cambios["departamento_residencia"]
        if pais is not None and pais not in PAISES_RESIDENCIA:
            raise ValueError("Selecciona un país del catálogo latinoamericano.")
        if departamento is not None and (pais is None or len(departamento) > 160 or (pais == "Bolivia" and departamento not in DEPARTAMENTOS_BOLIVIA)):
            raise ValueError("Selecciona un departamento válido de Bolivia y su país.")
    if "nacionalidad" in datos:
        valor = datos["nacionalidad"]
        if valor is not None and not isinstance(valor, str): raise ValueError("País de nacionalidad no válido.")
        valor = valor.strip() or None if valor is not None else None
        if valor is not None and valor not in PAISES_RESIDENCIA: raise ValueError("Selecciona un país de nacionalidad del catálogo.")
        cambios["nacionalidad"] = valor
    if "ano_incorporacion" in datos:
        ano = datos["ano_incorporacion"]
        if ano in (None, ""):
            ano = None
        elif isinstance(ano, bool) or not isinstance(ano, (str, int)):
            raise ValueError("El año de incorporación no es válido.")
        elif isinstance(ano, str):
            if not ano.isascii() or not ano.isdecimal():
                raise ValueError("El año de incorporación debe ser un entero.")
            ano = int(ano)
        if ano is not None and not 1 <= ano <= hoy.year:
            raise ValueError("El año de incorporación debe ser positivo y no futuro.")
        cambios["ano_incorporacion"] = ano
    if "fecha_incorporacion" in datos:
        valor = datos["fecha_incorporacion"]
        if valor in (None, ""):
            cambios["fecha_incorporacion"] = None
            if existentes.get("fecha_incorporacion"):
                cambios.update(ano_incorporacion=None, antiguedad_desde=None)
        else:
            if not isinstance(valor, str): raise ValueError("La fecha de incorporación no es válida.")
            fecha = date.fromisoformat(valor)
            if fecha.isoformat() != valor or fecha > hoy: raise ValueError("La fecha de incorporación debe ser válida y no futura.")
            if "ano_incorporacion" in datos and cambios.get("ano_incorporacion") != fecha.year:
                raise ValueError("El año no coincide con la fecha de incorporación.")
            if datos.get("antiguedad_desde") not in (None, "", valor):
                raise ValueError("La antigüedad desde debe coincidir con la incorporación.")
            cambios.update(fecha_incorporacion=valor, ano_incorporacion=fecha.year, antiguedad_desde=valor)
    elif existentes.get("fecha_incorporacion"):
        fecha = date.fromisoformat(existentes["fecha_incorporacion"])
        if "ano_incorporacion" in cambios and cambios["ano_incorporacion"] != fecha.year:
            raise ValueError("Edita la fecha de incorporación para cambiar su año.")
        if "antiguedad_desde" in datos and datos["antiguedad_desde"] != fecha.isoformat():
            raise ValueError("Edita la fecha de incorporación para cambiar la antigüedad desde.")
    return cambios


def antiguedad_calculada(ano, hoy=None):
    return None if ano is None else (hoy or date.today()).year - ano
