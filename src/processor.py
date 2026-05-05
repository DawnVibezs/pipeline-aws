import csv
import io
import json
import logging
 
logger = logging.getLogger(__name__)
 
 
def process_file(raw_content: str, file_type: str) -> list[dict]:
    """
    Faz o parse do conteúdo bruto e retorna uma lista de registros (dicts).
    Suporta CSV e JSON.
    """
    if file_type == "csv":
        return _parse_csv(raw_content)
    elif file_type == "json":
        return _parse_json(raw_content)
    else:
        raise ValueError(f"Tipo de arquivo não suportado: {file_type}")
 
 
def _parse_csv(content: str) -> list[dict]:
    """
    Lê um CSV e retorna lista de dicts.
    - Remove espaços extras dos nomes de colunas
    - Ignora linhas completamente vazias
    """
    reader  = csv.DictReader(io.StringIO(content))
    records = []
 
    # Normaliza headers: remove espaços e converte pra lowercase
    reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]
 
    for row in reader:
        # Ignora linhas completamente vazias
        if all(v.strip() == "" for v in row.values()):
            continue
 
        # Limpa espaços nos valores
        clean_row = {k: v.strip() for k, v in row.items()}
        records.append(clean_row)
 
    logger.info(f"CSV processado: {len(records)} registros encontrados")
    return records
 
 
def _parse_json(content: str) -> list[dict]:
    """
    Aceita dois formatos JSON:
    - Array de objetos: [{...}, {...}]
    - Objeto com chave 'data' ou 'records': {"data": [{...}]}
    """
    parsed = json.loads(content)
 
    if isinstance(parsed, list):
        records = parsed
    elif isinstance(parsed, dict):
        # Tenta encontrar a lista dentro de chaves comuns
        for key in ("data", "records", "items", "results"):
            if key in parsed and isinstance(parsed[key], list):
                records = parsed[key]
                break
        else:
            raise ValueError(
                "JSON inválido: esperado array ou objeto com chave "
                "'data', 'records', 'items' ou 'results'"
            )
    else:
        raise ValueError("JSON inválido: formato não reconhecido")
 
    logger.info(f"JSON processado: {len(records)} registros encontrados")
    return records