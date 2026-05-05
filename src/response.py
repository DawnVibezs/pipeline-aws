import json
from datetime import datetime, timezone


def ok(data: dict | list, status_code: int = 200) -> dict:
    """Resposta de sucesso padronizada."""
    return _build(status_code, {
        "success": True,
        "data":    data,
        "meta":    {"timestamp": _now()},
    })


def error(status_code: int, message: str, details: dict = None) -> dict:
    """Resposta de erro padronizada."""
    body = {
        "success": False,
        "error":   {"message": message},
        "meta":    {"timestamp": _now()},
    }
    if details:
        body["error"]["details"] = details

    return _build(status_code, body)


def _build(status_code: int, body: dict) -> dict:
    """Monta o envelope que o API Gateway espera."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",   # CORS — ajuste pra produção
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()