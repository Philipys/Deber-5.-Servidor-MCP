"""Servidor MCP Detective — Centinela.

Proporciona herramientas para la investigación de incidentes de seguridad simulados
en el sistema ficticio Centinela mediante el protocolo Model Context Protocol (MCP).
"""

from pathlib import Path
import json
from mcp.server import MCPServer

# Inicialización del servidor MCP
mcp = MCPServer("MCP Detective")

# Ruta absoluta al archivo de datos, resuelta desde __file__
RUTA_CASOS = Path(__file__).resolve().parent / "casos.json"

# Almacenamiento en memoria para alertas (solo vive durante la ejecución del proceso)
ALERTAS_MEMORIA: dict[str, dict] = {}

NIVELES_PERMITIDOS = {"bajo", "medio", "alto"}


def cargar_datos_casos() -> dict:
    """Carga y retorna los datos de casos desde casos.json."""
    if not RUTA_CASOS.exists():
        raise FileNotFoundError(f"Archivo de casos no encontrado en {RUTA_CASOS}")
    with open(RUTA_CASOS, "r", encoding="utf-8") as f:
        return json.load(f)


def obtener_resumen_casos() -> list[dict]:
    """Lógica pura: obtiene identificador, sistema y cantidad de eventos de cada caso."""
    datos = cargar_datos_casos()
    resumen = []
    for caso_id, info in datos.items():
        resumen.append({
            "caso_id": caso_id,
            "sistema": info.get("sistema", ""),
            "cantidad_eventos": len(info.get("eventos", []))
        })
    return resumen


def obtener_eventos_de_caso(caso_id: str) -> list[dict]:
    """Lógica pura: consulta los eventos de un caso específico."""
    if not caso_id or not isinstance(caso_id, str):
        raise ValueError("El identificador del caso debe ser una cadena no vacía.")

    datos = cargar_datos_casos()
    if caso_id not in datos:
        raise ValueError(f"El caso '{caso_id}' no existe en el sistema.")

    return datos[caso_id].get("eventos", [])


def registrar_alerta_en_memoria(caso_id: str, nivel: str, motivo: str) -> dict:
    """Lógica pura: valida y registra una alerta en memoria."""
    if not caso_id or not isinstance(caso_id, str):
        raise ValueError("El caso_id debe ser una cadena de texto válida.")

    datos = cargar_datos_casos()
    if caso_id not in datos:
        raise ValueError(f"El caso '{caso_id}' no existe en el sistema.")

    if not nivel or not isinstance(nivel, str) or nivel.lower().strip() not in NIVELES_PERMITIDOS:
        raise ValueError(f"Nivel de alerta inválido '{nivel}'. Debe ser exclusivamente 'bajo', 'medio' o 'alto'.")
    nivel_normalizado = nivel.lower().strip()

    if not motivo or not isinstance(motivo, str) or not motivo.strip():
        raise ValueError("El motivo no puede estar vacío ni contener solo espacios en blanco.")
    motivo_limpio = motivo.strip()

    if caso_id in ALERTAS_MEMORIA:
        raise ValueError(f"Ya existe una alerta registrada para el caso '{caso_id}'. No se permiten duplicados.")

    registro = {
        "caso_id": caso_id,
        "nivel": nivel_normalizado,
        "motivo": motivo_limpio,
        "estado": "registrada"
    }
    ALERTAS_MEMORIA[caso_id] = registro
    return registro


def reiniciar_alertas() -> None:
    """Limpia el almacenamiento en memoria (utilizado para pruebas aisladas)."""
    ALERTAS_MEMORIA.clear()


# ==============================================================================
# Herramientas MCP (@mcp.tool)
# ==============================================================================

@mcp.tool()
def listar_casos() -> list[dict]:
    """Lista todos los casos disponibles en el sistema con su identificador, sistema y cantidad de eventos.
    
    No emite clasificaciones ni conclusiones sobre los incidentes.
    """
    return obtener_resumen_casos()


@mcp.tool()
def consultar_eventos(caso_id: str) -> list[dict]:
    """Devuelve los registros exactos de eventos asociados a un caso específico.
    
    Lanza un error explícito si el identificador del caso no existe.
    """
    return obtener_eventos_de_caso(caso_id)


@mcp.tool()
def registrar_alerta(caso_id: str, nivel: str, motivo: str) -> dict:
    """Registra una alerta de seguridad en memoria para un caso existente.
    
    Valida que el caso exista, que el nivel sea 'bajo', 'medio' o 'alto', que el motivo
    tenga contenido real y que no exista una alerta previa para el mismo caso.
    """
    return registrar_alerta_en_memoria(caso_id, nivel, motivo)


if __name__ == "__main__":
    mcp.run(transport="stdio")
