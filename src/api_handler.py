import json
import logging

from auth import validate_api_key
from routes import route_request
from response import error

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Entry point da API Gateway.
    Fluxo:
      1. Valida a API Key no header
      2. Roteia para o handler correto
      3. Retorna resposta padronizada
    """
    method = event.get("httpMethod", "")
    path   = event.get("path", "")

    logger.info(json.dumps({
        "event":  "api_request",
        "method": method,
        "path":   path,
    }))

    # 1. Autenticação
    headers     = event.get("headers") or {}
    api_key     = headers.get("x-api-key") or headers.get("X-Api-Key", "")
    valid, auth_error = validate_api_key(api_key)

    if not valid:
        logger.warning(json.dumps({"event": "unauthorized", "reason": auth_error}))
        return error(401, auth_error)

    # 2. Roteamento
    try:
        return route_request(method, path, event)
    except Exception as exc:
        logger.error(json.dumps({"event": "unhandled_error", "error": str(exc)}))
        return error(500, "Erro interno do servidor")