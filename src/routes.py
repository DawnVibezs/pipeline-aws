import logging
import os
import re

from storage import get_job, list_jobs
from response import ok, error

logger = logging.getLogger(__name__)

DYNAMO_TABLE = os.environ["DYNAMO_TABLE"]

# Padrão de UUID para validar o job_id na URL
_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def route_request(method: str, path: str, event: dict) -> dict:
    """
    Roteia a requisição para o handler correto com base em method + path.

    Rotas disponíveis:
      GET /results          → lista todos os jobs (com paginação)
      GET /results/{job_id} → busca um job específico
    """

    # GET /results
    if method == "GET" and path == "/results":
        return _handle_list(event)

    # GET /results/{job_id}
    if method == "GET" and path.startswith("/results/"):
        job_id = path.split("/results/")[-1].strip("/")
        return _handle_get(job_id)

    return error(404, f"Rota não encontrada: {method} {path}")


# ─── Handlers ─────────────────────────────────────────────────────────────────

def _handle_get(job_id: str) -> dict:
    """GET /results/{job_id} — busca um job pelo ID."""

    # Valida formato do job_id antes de bater no banco
    if not _UUID_PATTERN.match(job_id.lower()):
        return error(400, f"job_id inválido: '{job_id}'. Deve ser um UUID v4.")

    logger.info(f"Buscando job: {job_id}")
    job = get_job(DYNAMO_TABLE, job_id)

    if not job:
        return error(404, f"Job '{job_id}' não encontrado")

    return ok(job)


def _handle_list(event: dict) -> dict:
    """
    GET /results — lista todos os jobs com paginação via cursor.

    Query params suportados:
      limit          → máximo de itens por página (padrão: 20, máximo: 100)
      last_evaluated → cursor para próxima página (retornado pela API)
      status         → filtro por status: SUCCESS | FAILED
    """
    params = event.get("queryStringParameters") or {}

    # Paginação
    try:
        limit = min(int(params.get("limit", 20)), 100)
    except ValueError:
        return error(400, "Parâmetro 'limit' deve ser um número inteiro")

    last_evaluated = params.get("last_evaluated")
    status_filter  = params.get("status")

    # Valida filtro de status se fornecido
    if status_filter and status_filter not in ("SUCCESS", "FAILED"):
        return error(400, "Parâmetro 'status' deve ser 'SUCCESS' ou 'FAILED'")

    logger.info(json_log("list_jobs", limit=limit, status=status_filter))

    jobs, next_cursor = list_jobs(
        table_name=DYNAMO_TABLE,
        limit=limit,
        last_evaluated=last_evaluated,
        status_filter=status_filter,
    )

    payload = {
        "items":      jobs,
        "count":      len(jobs),
        "next_cursor": next_cursor,  # None se não há próxima página
    }

    return ok(payload)


def json_log(event: str, **kwargs) -> str:
    import json
    return json.dumps({"event": event, **kwargs})