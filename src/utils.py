from datetime import datetime, timezone


def detect_file_type(object_key: str) -> str:
    """
    Detecta o tipo do arquivo pela extensão do objeto S3.
    Lança ValueError se o tipo não for suportado.
    """
    key_lower = object_key.lower()

    if key_lower.endswith(".csv"):
        return "csv"
    elif key_lower.endswith(".json"):
        return "json"
    else:
        raise ValueError(
            f"Extensão não suportada para '{object_key}'. "
            "Use arquivos .csv ou .json"
        )


def build_job_result(
    job_id: str,
    source_file: str,
    status: str,
    total: int,
    valid: int,
    error_count: int,
    output_key: str,
    started_at: str,
    error_message: str = None,
) -> dict:
    """
    Monta o dicionário de resultado do job para salvar no DynamoDB.
    Esse mesmo formato é retornado pela API de consulta (Fase 3).
    """
    finished_at = datetime.now(timezone.utc).isoformat()

    result = {
        "job_id":        job_id,
        "source_file":   source_file,
        "status":        status,           # SUCCESS | FAILED
        "total_records": total,
        "valid_records": valid,
        "error_count":   error_count,
        "output_key":    output_key,
        "started_at":    started_at,
        "finished_at":   finished_at,
        # TTL de 30 dias para limpeza automática no DynamoDB (boa prática)
        "ttl": int(
            datetime.now(timezone.utc).timestamp() + 60 * 60 * 24 * 30
        ),
    }

    if error_message:
        result["error_message"] = error_message

    return result