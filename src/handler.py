import json
import logging
import os
import uuid
from datetime import datetime, timezone
 
import boto3
 
from processor import process_file
from validator import validate_records
from storage import save_to_dynamodb
from utils import detect_file_type, build_job_result
 
# Logger estruturado — CloudWatch lê JSON nativamente
logger = logging.getLogger()
logger.setLevel(logging.INFO)
 
s3 = boto3.client("s3")
 
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
ERRORS_BUCKET    = os.environ["ERRORS_BUCKET"]
DYNAMO_TABLE     = os.environ["DYNAMO_TABLE"]
 
 
def lambda_handler(event, context):
    """
    Trigger: S3 PutObject no bucket raw/
    Fluxo:
      1. Lê o arquivo do S3
      2. Detecta o tipo (CSV ou JSON)
      3. Valida o schema
      4. Transforma os dados
      5. Salva em processed/ ou errors/
      6. Persiste resultado no DynamoDB
    """
    job_id    = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
 
    # Extrai informações do evento S3
    record     = event["Records"][0]
    src_bucket = record["s3"]["bucket"]["name"]
    object_key = record["s3"]["object"]["key"]
 
    logger.info(json.dumps({
        "job_id":     job_id,
        "event":      "job_started",
        "bucket":     src_bucket,
        "key":        object_key,
        "started_at": started_at,
    }))
 
    try:
        # 1. Lê o arquivo bruto do S3
        response    = s3.get_object(Bucket=src_bucket, Key=object_key)
        raw_content = response["Body"].read().decode("utf-8")
 
        # 2. Detecta tipo e faz o parse
        file_type = detect_file_type(object_key)
        records   = process_file(raw_content, file_type)
 
        # 3. Valida schema dos registros
        valid_records, errors = validate_records(records)
 
        # 4. Salva arquivo processado no S3
        output_key     = f"processed/{job_id}.json"
        output_content = json.dumps({
            "job_id":        job_id,
            "source_file":   object_key,
            "processed_at":  datetime.now(timezone.utc).isoformat(),
            "total_records": len(records),
            "valid_records": len(valid_records),
            "error_count":   len(errors),
            "data":          valid_records,
        }, ensure_ascii=False, indent=2)
 
        s3.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=output_key,
            Body=output_content.encode("utf-8"),
            ContentType="application/json",
        )
 
        # 5. Se houver erros de validação, salva relatório de erros
        if errors:
            error_key = f"errors/{job_id}_validation_errors.json"
            s3.put_object(
                Bucket=ERRORS_BUCKET,
                Key=error_key,
                Body=json.dumps({"job_id": job_id, "errors": errors}, indent=2).encode("utf-8"),
                ContentType="application/json",
            )
 
        # 6. Persiste resultado no DynamoDB
        result = build_job_result(
            job_id=job_id,
            source_file=object_key,
            status="SUCCESS",
            total=len(records),
            valid=len(valid_records),
            error_count=len(errors),
            output_key=output_key,
            started_at=started_at,
        )
        save_to_dynamodb(DYNAMO_TABLE, result)
 
        logger.info(json.dumps({
            "job_id":        job_id,
            "event":         "job_completed",
            "status":        "SUCCESS",
            "total_records": len(records),
            "valid_records": len(valid_records),
            "error_count":   len(errors),
        }))
 
        return {"statusCode": 200, "body": json.dumps(result)}
 
    
    except Exception as exc:
        # Qualquer erro inesperado: registra no DynamoDB como FAILED
        logger.error(json.dumps({
            "job_id": job_id,
            "event":  "job_failed",
            "error":  str(exc),
        }))
 
        error_key = f"errors/{job_id}_crash.txt"
        s3.put_object(
            Bucket=ERRORS_BUCKET,
            Key=error_key,
            Body=str(exc).encode("utf-8"),
        )
 
        result = build_job_result(
            job_id=job_id,
            source_file=object_key,
            status="FAILED",
            total=0,
            valid=0,
            error_count=1,
            output_key=error_key,
            started_at=started_at,
            error_message=str(exc),
        )
        save_to_dynamodb(DYNAMO_TABLE, result)
 
        raise  # Re-lança pra CloudWatch capturar
