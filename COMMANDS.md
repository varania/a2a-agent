# Guía de comandos

Referencia rápida de todos los comandos útiles del proyecto. Todos se ejecutan
desde la raíz del repositorio.

---

## Índice

1. [Instalar uv](#1-instalar-uv)
2. [Primer arranque](#2-primer-arranque)
3. [Servidor](#3-servidor)
4. [Cliente A2A](#4-cliente-a2a)
5. [Endpoints con curl](#5-endpoints-con-curl)
6. [Dependencias con uv](#6-dependencias-con-uv)
7. [Tests y cobertura](#7-tests-y-cobertura)
8. [Lint, formato y tipos](#8-lint-formato-y-tipos)
9. [Makefile](#9-makefile)
10. [Docker](#10-docker)
11. [Git y GitHub](#11-git-y-github)
12. [Solución de problemas](#12-solución-de-problemas)

---

## 1. Instalar uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Comprobar
uv --version
```

## 2. Primer arranque

```bash
git clone git@github.com:varania/a2a-agent.git
cd a2a-agent
git switch develop          # rama de trabajo

uv sync                     # crea .venv e instala todo desde uv.lock
cp .env.example .env        # edita .env y pon OPENAI_API_KEY

uv run a2a-agent            # servidor en http://127.0.0.1:9999
```

Verificación rápida:

```bash
curl -s http://127.0.0.1:9999/health
curl -s http://127.0.0.1:9999/.well-known/agent-card.json
```

## 3. Servidor

```bash
uv run a2a-agent                              # host/puerto desde .env
uv run a2a-agent --host 0.0.0.0 --port 8080   # sobrescribe host/puerto
uv run a2a-agent --reload                     # recarga en caliente (dev)
uv run a2a-agent --version                    # versión del paquete
uv run python -m a2a_agent                    # equivalente sin script

# Uvicorn directamente (útil para depurar)
uv run uvicorn a2a_agent.server.app:app --reload --host 127.0.0.1 --port 9999

# Variables de entorno puntuales
A2A_PORT=8000 A2A_LOG_LEVEL=DEBUG uv run a2a-agent
```

URLs del servidor:

| URL | Qué es |
| --- | --- |
| `http://127.0.0.1:9999/health` | Liveness probe |
| `http://127.0.0.1:9999/.well-known/agent-card.json` | Agent Card (descubrimiento A2A) |
| `http://127.0.0.1:9999/docs` | Swagger UI con los endpoints A2A |
| `http://127.0.0.1:9999/openapi.json` | Esquema OpenAPI |
| `http://127.0.0.1:9999/` | JSON-RPC 2.0 |

## 4. Cliente A2A

```bash
uv run a2a-agent-client "¿Cuánto es (120 * 3) / 4?"

# Contra otra URL
uv run a2a-agent-client --url http://localhost:8080 "hola"

# Conversación con memoria (mismo context-id)
uv run a2a-agent-client --context-id demo "Me llamo Víctor"
uv run a2a-agent-client --context-id demo "¿Cómo me llamo?"

# Alternativas
uv run python -m a2a_agent.client.cli "hola"
uv run python -c "import asyncio; from a2a_agent.client.cli import send_message; asyncio.run(send_message('http://127.0.0.1:9999', 'hola'))"
```

## 5. Endpoints con curl

```bash
# Salud
curl -s http://127.0.0.1:9999/health | jq

# Agent Card
curl -s http://127.0.0.1:9999/.well-known/agent-card.json | jq

# Rutas publicadas
curl -s http://127.0.0.1:9999/openapi.json | jq '.paths | keys'

# Documentación en el navegador
xdg-open http://127.0.0.1:9999/docs    # macOS: open ...
```

### JSON-RPC 2.0

Todas las peticiones necesitan la cabecera `A2A-Version: 1.0`.

```bash
# Enviar mensaje (bloqueante)
curl -sS -X POST http://127.0.0.1:9999/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "SendMessage",
    "params": {
      "message": {
        "messageId": "m1",
        "role": "ROLE_USER",
        "parts": [{"text": "¿Cuánto es 2+2?"}]
      }
    }
  }' | jq

# Enviar mensaje en streaming (SSE)
curl -N -sS -X POST http://127.0.0.1:9999/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -H 'Accept: text/event-stream' \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "SendStreamingMessage",
    "params": {
      "message": {
        "messageId": "m2",
        "role": "ROLE_USER",
        "parts": [{"text": "Cuéntame algo"}]
      }
    }
  }'

# Consultar una tarea
curl -sS -X POST http://127.0.0.1:9999/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{"jsonrpc":"2.0","id":"3","method":"GetTask","params":{"id":"TASK_ID"}}' | jq

# Cancelar una tarea
curl -sS -X POST http://127.0.0.1:9999/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{"jsonrpc":"2.0","id":"4","method":"CancelTask","params":{"id":"TASK_ID"}}' | jq
```

### HTTP+JSON / REST

```bash
# Enviar mensaje
curl -sS -X POST http://127.0.0.1:9999/message:send \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{
    "message": {
      "messageId": "m3",
      "role": "ROLE_USER",
      "parts": [{"text": "hola"}]
    }
  }' | jq

# Streaming
curl -N -sS -X POST http://127.0.0.1:9999/message:stream \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -H 'Accept: text/event-stream' \
  -d '{"message":{"messageId":"m4","role":"ROLE_USER","parts":[{"text":"hola"}]}}'

# Obtener tarea / listar tareas
curl -sS http://127.0.0.1:9999/tasks/TASK_ID -H 'A2A-Version: 1.0' | jq
curl -sS http://127.0.0.1:9999/tasks -H 'A2A-Version: 1.0' | jq
```

## 6. Dependencias con uv

```bash
uv sync                          # instala el entorno completo (dev incluido)
uv sync --frozen                 # igual, falla si uv.lock no está al día (CI)
uv sync --no-dev                 # solo dependencias de producción

uv add paquete                   # añade dependencia y actualiza el lock
uv add "a2a-sdk[grpc]"           # con extras
uv add --dev respx               # dependencia de desarrollo
uv remove paquete                # elimina dependencia

uv lock                          # regenera uv.lock
uv lock --check                  # verifica que el lock está actualizado
uv lock --upgrade                # actualiza todas las dependencias
uv lock --upgrade-package langchain   # actualiza solo una

uv tree                          # árbol de dependencias
uv pip list                      # paquetes instalados en .venv
uv python list                   # intérpretes disponibles
uv python pin 3.13              # fija la versión en .python-version

uv run python -c "import a2a_agent; print(a2a_agent.__version__)"
uv build                         # construye sdist + wheel en dist/
```

> `uv.lock` se versiona: no lo borres ni lo ignores. `uv add` y `uv lock` lo
> actualizan automáticamente.

## 7. Tests y cobertura

```bash
uv run pytest                          # toda la suite
uv run pytest -v                       # detallado
uv run pytest -q                       # resumido
uv run pytest -x                       # para en el primer fallo
uv run pytest --lf                     # solo los que fallaron la última vez

# Filtrar
uv run pytest -k calculator
uv run pytest tests/test_executor.py
uv run pytest tests/test_executor.py::test_executor_streams_artifacts_as_chunks

# Cobertura
uv run pytest --cov --cov-report=term-missing
uv run pytest --cov --cov-report=html
xdg-open htmlcov/index.html            # macOS: open ...
```

## 8. Lint, formato y tipos

```bash
uv run ruff check .                    # lint
uv run ruff check --fix .              # lint + autofix seguro
uv run ruff format .                   # formatea
uv run ruff format --check .           # comprueba sin modificar
uv run mypy                            # tipado estático (src + tests)
uv run mypy src/a2a_agent/server       # solo un paquete
```

## 9. Makefile

```bash
make help          # lista de objetivos
make sync          # uv sync
make run           # servidor
make dev           # servidor con --reload
make test          # pytest
make cov           # pytest + cobertura en terminal
make lint          # ruff check
make format        # ruff format
make typecheck     # mypy
make check         # lint + typecheck + tests (lo que corre la CI)
make docker-build  # docker build
make docker-run    # docker run con .env
make clean         # limpia caches y artefactos
```

## 10. Docker

```bash
docker build -t a2a-agent .
docker run --rm -p 9999:9999 --env-file .env a2a-agent

# Sin archivo .env
docker run --rm -p 9999:9999 \
  -e OPENAI_API_KEY=sk-... \
  -e A2A_PUBLIC_URL=http://localhost:9999 \
  a2a-agent

# En segundo plano
docker run -d --name a2a-agent --restart unless-stopped \
  -p 9999:9999 --env-file .env a2a-agent

docker logs -f a2a-agent
docker exec -it a2a-agent sh
docker stop a2a-agent && docker rm a2a-agent

# Reconstruir sin caché
docker build --no-cache -t a2a-agent .
```

El contenedor corre como usuario `app` (no root) y expone un `HEALTHCHECK`
contra `/health`.

## 11. Git y GitHub

```bash
git status
git switch develop
git pull --rebase

# Nueva feature
git switch -c feature/mi-herramienta
git add -A
git commit -m "feat: add mi-herramienta tool"
git push -u origin feature/mi-herramienta

# Pull request contra develop
gh pr create --base develop --fill
gh pr status
gh pr view --web

# Limpieza
git switch develop && git pull
git branch -d feature/mi-herramienta

# Historial
git log --oneline --graph --decorate -10
git diff develop...origin/develop
```

> La rama por defecto del repositorio y la rama de trabajo es **`develop`**.
> `main` queda para releases.

## 12. Solución de problemas

| Problema | Solución |
| --- | --- |
| `Missing credentials` al invocar al agente | Define `OPENAI_API_KEY` en `.env`, o `OPENAI_BASE_URL` + `OPENAI_API_KEY=ollama` para un servidor local |
| `uv: command not found` | `source "$HOME/.local/bin/env"` |
| `Address already in use` | `ss -ltnp \| grep 9999` y cambia el puerto con `A2A_PORT=8000` |
| El Agent Card anuncia una URL incorrecta | Define `A2A_PUBLIC_URL=https://mi-dominio` |
| El modelo no existe | Usa el formato `proveedor:modelo` en `A2A_MODEL` (p. ej. `openai:gpt-4o-mini`) |
| `ZoneInfoNotFoundError` en Windows | `uv add tzdata` (el tool ya cae a UTC si falla) |
| Los cambios no se recargan | Arranca con `uv run a2a-agent --reload` |
| Error de versión de Python | `uv python pin 3.13 && uv sync` |
| `uv.lock` desactualizado en CI | `uv lock && git add uv.lock` |

### Usar Ollama / vLLM / LM Studio

```bash
# .env
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
A2A_MODEL=openai:llama3.2
```

```bash
ollama serve
ollama pull llama3.2
uv run a2a-agent
```
