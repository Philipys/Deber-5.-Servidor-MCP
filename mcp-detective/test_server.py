"""Pruebas unitarias para el Servidor MCP Detective.

Verifica el comportamiento de las herramientas y la validación en el servidor
usando pytest.
"""

import pytest
from server import (
    listar_casos,
    consultar_eventos,
    registrar_alerta,
    reiniciar_alertas,
)


@pytest.fixture(autouse=True)
def limpiar_estado_memoria():
    """Garantiza que el almacenamiento en memoria esté limpio antes y después de cada prueba."""
    reiniciar_alertas()
    yield
    reiniciar_alertas()


def test_listar_casos_retorna_todos_los_casos():
    """1. listar_casos() devuelve exactamente INC-001, INC-002 e INC-003 con sus conteos."""
    casos = listar_casos()
    assert isinstance(casos, list)
    assert len(casos) == 3

    ids = [c["caso_id"] for c in casos]
    assert "INC-001" in ids
    assert "INC-002" in ids
    assert "INC-003" in ids

    # Validar conteos esperados
    mapa = {c["caso_id"]: c for c in casos}
    assert mapa["INC-001"]["cantidad_eventos"] == 2
    assert mapa["INC-002"]["cantidad_eventos"] == 6
    assert mapa["INC-003"]["cantidad_eventos"] == 5


def test_consultar_eventos_caso_valido():
    """Verifica que consultar_eventos("INC-002") devuelva sus seis eventos exactos."""
    eventos = consultar_eventos("INC-002")
    assert isinstance(eventos, list)
    assert len(eventos) == 6
    for evento in eventos:
        assert evento["usuario"] == "admin"
        assert evento["evento"] == "LOGIN_FAILED"
        assert evento["ip"] == "203.0.113.25"


def test_consultar_eventos_caso_desconocido_lanza_error():
    """2. consultar_eventos('INC-999') produce un error explícito (ValueError)."""
    with pytest.raises(ValueError, match="no existe"):
        consultar_eventos("INC-999")


def test_registrar_alerta_valida():
    """3. registrar_alerta con parámetros válidos registra correctamente."""
    resultado = registrar_alerta(
        caso_id="INC-003",
        nivel="alto",
        motivo="Cuatro fallos y un acceso exitoso desde la misma IP; requiere investigación"
    )
    assert resultado["caso_id"] == "INC-003"
    assert resultado["nivel"] == "alto"
    assert resultado["estado"] == "registrada"
    assert "Cuatro fallos" in resultado["motivo"]


def test_registrar_alerta_duplicada_falla():
    """4. Un segundo registro del mismo caso en la misma instancia se rechaza como duplicado."""
    registrar_alerta(
        caso_id="INC-003",
        nivel="alto",
        motivo="Primera alerta legítima"
    )

    with pytest.raises(ValueError, match="duplicados|Ya existe una alerta"):
        registrar_alerta(
            caso_id="INC-003",
            nivel="medio",
            motivo="Intento de alerta duplicada"
        )


def test_registrar_alerta_nivel_invalido():
    """Validación de niveles: rechaza niveles distintos de bajo/medio/alto."""
    with pytest.raises(ValueError, match="Nivel de alerta inválido"):
        registrar_alerta(
            caso_id="INC-002",
            nivel="critico",
            motivo="Intentos repetidos sospechosos"
        )


def test_registrar_alerta_motivo_en_blanco():
    """Validación de motivo: rechaza motivos vacíos o con solo espacios."""
    with pytest.raises(ValueError, match="no puede estar vacío"):
        registrar_alerta(
            caso_id="INC-002",
            nivel="medio",
            motivo="   "
        )
