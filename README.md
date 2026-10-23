# A2A Agent · LangChain + LangGraph + FastAPI

Agente de ejemplo listo para producción que expone un modelo de lenguaje a
través del protocolo **[A2A (Agent2Agent)](https://a2a-protocol.org)**, usando
[LangChain](https://python.langchain.com) / [LangGraph](https://langchain-ai.github.io/langgraph/)
como motor del agente y [FastAPI](https://fastapi.tiangolo.com) como servidor.

El agente sabe conversar, hacer cálculos exactos con la herramienta
`calculator` y consultar la fecha/hora actual (`get_current_time`). Añadir
nuevas capacidades consiste en crear una `@tool` y registrarla en
`src/a2a_agent/tools/__init__.py`.

---

## Stack

| Pieza | Tecnología |
| --- | --- |
| Protocolo | [`a2a-sdk`](https://pypi.org/project/a2a-sdk/) 1.x (spec A2A 1.0 + compatibilidad 0.3) |
| Agente | `langchain` 1.x (`create_agent`) + `langgraph` |
| Modelo | `langchain-openai` (OpenAI, Ollama, vLLM, LM Studio…) |
| Servidor | `fastapi` + `uvicorn` |
| Configuración | `pydantic-settings` (`.env` + variables de entorno) |
| Gestor de paquetes | [`uv`](https://docs.astral.sh/uv/) |
| Calidad | `pytest`, `ruff`, `mypy` |

---

## Requisitos

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Puesta en marcha

```bash
# 1. Dependencias (crea .venv y respeta uv.lock)
uv sync

# 2. Configuración
cp .env.example .env
#    edita .env y define OPENAI_API_KEY (o OPENAI_BASE_URL para Ollama/vLLM)

# 3. Arranca el agente
uv run a2a-agent
#    → http://127.0.0.1:9999

# 4. Prueba rápida con el cliente incluido
uv run a2a-agent-client "¿Cuánto es (120 * 3) / 4?"
```

El **Agent Card** (documento de descubrimiento) queda publicado en:

```
http://127.0.0.1:9999/.well-known/agent-card.json
```

Y la documentación OpenAPI (incluye los endpoints A2A) en
`http://127.0.0.1:9999/docs`.

---

## Estructura del proyecto

```
a2a-agent/
├── src/a2a_agent/
│   ├── __main__.py          # Entry point: `a2a-agent`
│   ├── config.py            # Settings (pydantic-settings)
│   ├── logging.py           # Logging homogéneo
│   ├── agent/
│   │   ├── agent.py         # LangGraph agent + streaming async
│   │   └── prompts.py       # System prompt
│   ├── tools/
│   │   ├── calculator.py    # Herramienta de cálculo seguro
│   │   └── clock.py         # Herramienta de fecha/hora
│   ├── server/
│   │   ├── app.py           # FastAPI app factory + rutas A2A
│   │   ├── card.py          # Agent Card (skills, interfaces, capabilities)
│   │   └── executor.py      # AgentExecutor: A2A ⇄ LangChain
│   └── client/
│       └── cli.py           # Cliente A2A de prueba (`a2a-agent-client`)
├── tests/                   # pytest (unitarios + integración ligera)
├── .env.example
├── COMMANDS.md              # referencia completa de comandos
├── Dockerfile
├── Makefile
├── pyproject.toml           # Dependencias + configuración de herramientas
└── uv.lock
```

La estructura sigue el **layout canónico `src/`**: el paquete vive en
`src/a2a_agent` para que los tests se ejecuten contra la versión instalada y no
contra el árbol de trabajo. Cada capa tiene una única responsabilidad:

- **`agent/`** no conoce A2A; solo LangChain.
- **`server/`** no contiene lógica del LLM; traduce entre el protocolo y el agente.
- **`tools/`** agrupa las capacidades expuestas al modelo.
- **`client/`** es una utilidad de desarrollo, no forma parte del servidor.

---

## Cómo funciona

```
Cliente A2A ──► GET  /.well-known/agent-card.json   (descubre el agente)
            ──► POST /            (JSON-RPC 2.0)
            ──► POST /message:send      (HTTP+JSON/REST)
                        │
                DefaultRequestHandler
                        │
              LangChainAgentExecutor
                        │
              LangChainAgent (LangGraph)
                        │
                LLM + tools (calculator, clock)
```

1. El cliente descubre el agente por su **Agent Card**.
2. Envía un `SendMessageRequest` (o `message/stream`).
3. `LangChainAgentExecutor` crea/recupera la tarea A2A y publica el estado
   `working`.
4. `LangChainAgent.astream()` ejecuta el grafo de LangGraph y emite tokens.
5. El executor los publica como **chunks de artifact** (`append=True`) y cierra
   con `last_chunk=True` + estado `completed`.
6. La memoria conversacional se guarda por `context_id` (checkpoint de
   LangGraph), así que reutilizar el mismo contexto mantiene el hilo.

---

## Configuración

Todas las variables usan el prefijo `A2A_` (o se definen en `.env`).

| Variable | Por defecto | Descripción |
| --- | --- | --- |
| `A2A_AGENT_NAME` | `LangChain A2A Agent` | Nombre visible en el Agent Card |
| `A2A_AGENT_DESCRIPTION` | — | Descripción del agente |
| `A2A_AGENT_VERSION` | `0.1.0` | Versión del agente |
| `A2A_HOST` | `0.0.0.0` | Dirección de escucha |
| `A2A_PORT` | `9999` | Puerto |
| `A2A_PUBLIC_URL` | — | URL pública anunciada (reverse proxy, contenedores) |
| `A2A_LOG_LEVEL` | `INFO` | Nivel de logging |
| `A2A_MODEL` | `openai:gpt-4o-mini` | Identificador de modelo de LangChain |
| `A2A_TEMPERATURE` | `0.0` | Temperatura del modelo |
| `A2A_MAX_TOKENS` | — | Límite de tokens de salida |
| `A2A_STREAMING` | `true` | Anuncia streaming en el Agent Card |
| `A2A_CORS_ORIGINS` | `[]` | Orígenes CORS permitidos (JSON) |

El proveedor del modelo se configura con las variables estándar de
`langchain-openai`:

```bash
OPENAI_API_KEY=sk-...
# Para un servidor compatible con OpenAI (Ollama, vLLM, LM Studio…):
OPENAI_BASE_URL=http://localhost:11434/v1
A2A_MODEL=openai:llama3.2
```

---

## Comandos

Los más habituales:

```bash
uv sync                          # instala el entorno
uv run a2a-agent                 # servidor
uv run a2a-agent --reload        # servidor con recarga en caliente
uv run a2a-agent-client "hola"   # cliente A2A de prueba

uv run pytest                    # tests
uv run pytest --cov              # tests + cobertura
uv run ruff check .              # lint
uv run ruff format .             # formato
uv run mypy                      # tipado estático
make check                       # lint + tipos + tests
```

📖 **Referencia completa: [COMMANDS.md](COMMANDS.md)** — instalación de `uv`,
todas las flags del servidor y del cliente, ejemplos `curl` de cada endpoint
(JSON-RPC y REST), gestión de dependencias, tests, Docker, flujo de git y
solución de problemas.

## Docker

```bash
docker build -t a2a-agent .
docker run --rm -p 9999:9999 --env-file .env a2a-agent
```

---

## Referencias

- [Especificación A2A](https://a2a-protocol.org/latest/specification/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- [LangChain · Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [uv](https://docs.astral.sh/uv/)
