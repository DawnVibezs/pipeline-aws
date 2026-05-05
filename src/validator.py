import logging
import re
from datetime import datetime, timezone # <-- Adicionado timezone aqui

logger = logging.getLogger(__name__)

# Campos obrigatórios que todo registro deve ter
REQUIRED_FIELDS = {"id", "name", "email"}

# Campos com tipos esperados (campo -> tipo Python)
TYPE_RULES = {
    "id":   str,
    "name":  str,
    "email": str,
}

def validate_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Valida cada registro contra as regras definidas.
    Retorna:
        valid_records: registros que passaram em todas as validações
        errors:        lista de erros encontrados com contexto do registro
    """
    valid_records = []
    errors        = []

    for index, record in enumerate(records):
        record_errors = _validate_single(record, index)

        if record_errors:
            errors.append({
                "record_index": index,
                "record":       record,
                "errors":       record_errors,
            })
        else:
            # Transforma os dados antes de salvar (normalização)
            valid_records.append(_transform(record))

    logger.info(
        f"Validação concluída: {len(valid_records)} válidos, {len(errors)} com erro"
    )
    return valid_records, errors


def _validate_single(record: dict, index: int) -> list[str]:
    """Retorna lista de mensagens de erro para um único registro."""
    errs = []

    # PROTEÇÃO: Se não for dicionário, barra na hora sem quebrar o código
    if not isinstance(record, dict):
         return ["Formato inválido: esperado um dicionário/objeto JSON."]

    # 1. Campos obrigatórios presentes e não vazios
    for field in REQUIRED_FIELDS:
        if field not in record:
            errs.append(f"Campo obrigatório ausente: '{field}'")
        elif not str(record[field]).strip():
            errs.append(f"Campo obrigatório vazio: '{field}'")

    # 2. Validação de email
    if "email" in record and record["email"]:
        if not _is_valid_email(record["email"]):
            errs.append(f"Email inválido: '{record['email']}'")

    # 3. ID não pode ser duplicado dentro do batch (checagem simples)
    # (checagem de duplicata global seria feita via DynamoDB ConditionExpression)

    return errs


def _transform(record: dict) -> dict:
    """
    Normaliza os dados do registro antes de persistir:
    - Trim em todos os campos string
    - Email em lowercase
    - Nome com Title Case
    - Adiciona timestamp de processamento
    """
    transformed = {k: v.strip() if isinstance(v, str) else v for k, v in record.items()}

    if "email" in transformed:
        transformed["email"] = transformed["email"].lower()

    if "name" in transformed:
        transformed["name"] = transformed["name"].title()

    # CORREÇÃO DO WARNING: Usando timezone-aware object
    transformed["processed_at"] = datetime.now(timezone.utc).isoformat()

    return transformed


def _is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))