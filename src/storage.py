import json
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")


def save_to_dynamodb(table_name: str, item: dict) -> None:
    """
    Persiste o resultado do job no DynamoDB.
    Usa condition expression para evitar sobrescrever jobs existentes.
    """
    table = dynamodb.Table(table_name)

    # DynamoDB não aceita float — converte para Decimal
    item = _sanitize_for_dynamo(item)

    try:
        table.put_item(
            Item=item,
            ConditionExpression=Attr("job_id").not_exists(),  # Idempotência
        )
        logger.info(f"Job {item['job_id']} salvo no DynamoDB com sucesso")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # Job já existe — não é um erro crítico, apenas loga
            logger.warning(f"Job {item['job_id']} já existe no DynamoDB, ignorando")
        else:
            logger.error(f"Erro ao salvar no DynamoDB: {e}")
            raise


def list_jobs(
    table_name: str,
    limit: int = 20,
    last_evaluated: str = None,
    status_filter: str = None,
) -> tuple[list[dict], str | None]:
    """
    Lista jobs com paginação via cursor (LastEvaluatedKey do DynamoDB).

    Parâmetros:
        limit          → máximo de itens retornados
        last_evaluated → cursor da página anterior (string JSON base64)
        status_filter  → filtra por 'SUCCESS' ou 'FAILED'

    Retorna (items, next_cursor) onde next_cursor é None se não há mais páginas.
    """
    import base64

    table  = dynamodb.Table(table_name)
    kwargs = {"Limit": limit}

    # Reconstrói o cursor de paginação do DynamoDB
    if last_evaluated:
        try:
            raw = base64.b64decode(last_evaluated.encode()).decode()
            kwargs["ExclusiveStartKey"] = json.loads(raw)
        except Exception:
            raise ValueError("Cursor 'last_evaluated' inválido")

    # Filtro por status (FilterExpression — aplicado após leitura da página)
    if status_filter:
        from boto3.dynamodb.conditions import Attr
        kwargs["FilterExpression"] = Attr("status").eq(status_filter)

    response = table.scan(**kwargs)
    items    = [_deserialize_from_dynamo(i) for i in response.get("Items", [])]

    # Monta cursor pra próxima página (None se acabou)
    next_cursor = None
    if "LastEvaluatedKey" in response:
        raw         = json.dumps(response["LastEvaluatedKey"])
        next_cursor = base64.b64encode(raw.encode()).decode()

    return items, next_cursor


def get_job(table_name: str, job_id: str) -> dict | None:
    """
    Busca um job pelo ID. Usado pela API de consulta (Fase 3).
    Retorna None se não encontrado.
    """
    table = dynamodb.Table(table_name)

    response = table.get_item(Key={"job_id": job_id})
    item     = response.get("Item")

    if item:
        return _deserialize_from_dynamo(item)
    return None


def _sanitize_for_dynamo(obj):
    """Converte floats para Decimal recursivamente (requisito do DynamoDB)."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _sanitize_for_dynamo(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_dynamo(i) for i in obj]
    return obj


def _deserialize_from_dynamo(obj):
    """Converte Decimal de volta pra int/float ao ler do DynamoDB."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _deserialize_from_dynamo(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deserialize_from_dynamo(i) for i in obj]
    return obj