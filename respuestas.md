# Respuestas — Deber 5: MCP Detective: ¿qué pasó en el sistema?

**Programación Asistida de Aplicaciones · USFQ**  
**Estudiante:** Felipe Anrrango  
**Profesor:** Jose David Vega Sánchez  

---

## 1. Arquitectura

### Roles de cada componente

* **LLM (Modelo de Lenguaje):**  
  Interpreta el lenguaje natural y el contexto de la solicitud del usuario. Razona sobre qué herramientas necesita invocar (`listar_casos`, `consultar_eventos`, `registrar_alerta`) y formula los argumentos correspondientes en base a los esquemas recibidos. No ejecuta código, no accede a archivos ni tiene persistencia o estado del sistema.

* **Harness / Host (Entorno del Agente):**  
  Es la plataforma anfitriona (en este caso, Antigravity IDE). Gestiona la interfaz con el usuario, coordina el ciclo de vida del agente, mantiene el historial de la conversación y orquesta la comunicación entre el LLM y los clientes de herramientas.

* **Cliente MCP:**  
  Es el módulo integrado en el host que implementa el protocolo estándar Model Context Protocol. Se encarga de conectarse al servidor MCP, descubrir las herramientas disponibles (*tool discovery* con sus esquemas JSON Schema), serializar las llamadas propuestas por el LLM en mensajes JSON-RPC a través de `stdio` y deserializar las respuestas devueltas por el servidor.

* **Servidor MCP (`server.py`):**  
  Es un proceso independiente en Python que expone las tres herramientas mediante el SDK de MCP. Escucha peticiones por `stdio`, valida rigurosamente los argumentos de forma determinista, consulta el archivo local `casos.json`, mantiene el registro de alertas en memoria y devuelve los resultados estructurados o errores al cliente.

### ¿Cuál ejecutó realmente Python?
El **servidor MCP (`server.py`)**. Es el único componente que corre como un proceso de Python local en el sistema operativo, interactúa con el sistema de archivos (`casos.json`) y gestiona el almacenamiento en memoria del proceso durante la sesión.

---

## 2. Evidencia

### ¿Por qué `INC-003` merece investigación?
El caso `INC-003` (sistema `panel_administracion`) muestra una secuencia altamente sospechosa:
1. Cuatro intentos fallidos consecutivos de inicio de sesión (`LOGIN_FAILED`) entre las `03:00` y las `03:03`.
2. Un intento exitoso inmediato (`LOGIN_SUCCESS`) a las `03:04`.
3. Todos los intentos provienen de la misma dirección IP (`192.0.2.50`) y utilizan la cuenta privilegiada `admin`.
4. La actividad ocurre a las 03:00 AM, un horario atípico de baja concurrencia.

Este patrón coincide con una técnica típica de adivinación de credenciales o ataque de fuerza bruta controlado. Por ende, amerita una alerta de nivel **alto** para que el equipo de seguridad revise la actividad.

### ¿Por qué los logs no permiten afirmar con certeza que hubo una intrusión?
Porque los registros de eventos disponibles solo evidencian intentos y un resultado de autenticación, pero carecen de telemetría contextual profunda:
* No se dispone de logs de actividad posterior a las 03:04 para comprobar si se ejecutaron comandos o consultas indebidas.
* No se puede descartar un falso positivo operacional (por ejemplo, el administrador legítimo olvidando temporalmente su contraseña o cometiendo errores de tipeo de madrugada).
* No hay datos de factores adicionales como autenticación multifactor (MFA), análisis de huella de dispositivo o geolocalización.  

Un patrón anómalo en un log **justifica una investigación urgente, pero no constituye por sí solo una prueba concluyente de vulneración o compromiso del sistema**.

---

## 3. Validación y Seguridad

### ¿Quién rechaza `INC-999` o los parámetros inválidos?
El **servidor MCP**, de manera determinista en el código Python de `server.py`:
* Al consultar `consultar_eventos("INC-999")` o registrar alertas sobre un caso inexistente, la función `obtener_eventos_de_caso` verifica si la clave existe en el diccionario cargado desde `casos.json`. Al no existir, levanta explícitamente una excepción `ValueError("El caso 'INC-999' no existe en el sistema.")`.
* Los niveles inválidos (distintos de `bajo`, `medio`, `alto`) y los motivos vacíos o con solo espacios son igualmente rechazados mediante `ValueError`.

### ¿Por qué no es seguro confiar solo en que el modelo genere argumentos correctos?
1. **Naturaleza probabilística:** Los LLMs operan por predicción de tokens; no garantizan determinismo estricto y pueden sufrir alucinaciones (inventar IDs como `INC-999` o inventar niveles como `crítico` o `urgente`).
2. **Manipulación o Prompt Injection:** Un usuario malintencionado o datos no confiables en el prompt podrían inducir al modelo a omitir validaciones o enviar parámetros dañinos.
3. **Principio de defensa en profundidad y límites de confianza:** El servidor MCP representa la frontera con el sistema real y los datos. Es responsabilidad indelegable del servidor validar tipos, formatos, existencia y reglas de negocio antes de procesar o modificar el estado, asegurando la integridad del sistema sin depender de la "buena conducta" del modelo.

---

## Información del Entorno y Guía de Conexión

* **Agente utilizado:** Antigravity IDE (Gemini 3.8 Flash) con cliente MCP integrado.
* **Comprobación de conexión:** Se verificó mediante la negociación inicial de capacidades (*discovery*), donde el host reconoció e indexó las herramientas `listar_casos`, `consultar_eventos` y `registrar_alerta`, permitiendo su ejecución controlada y trazable.

### Instrucciones breves de ejecución

1. **Instalación de dependencias:**
   ```bash
   pip install "mcp[cli]>=2,<3" pytest
   ```

2. **Ejecución de pruebas unitarias:**
   ```bash
   pytest mcp-detective -q
   ```

3. **Iniciar MCP Inspector (pruebas manuales sin LLM):**
   ```bash
   mcp dev mcp-detective/server.py
   ```

4. **Conectar el servidor MCP al host/agente (configuración `stdio`):**
   ```json
   {
     "mcpServers": {
       "mcp-detective": {
         "command": "python",
         "args": ["<RUTA_ABSOLUTA>/mcp-detective/server.py"]
       }
     }
   }
   ```
