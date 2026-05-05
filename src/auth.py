import hashlib
import hmac
import logging
import os

logger = logging.getLogger(__name__)

# A API Key válida vem de variável de ambiente (nunca hardcoded!)
# Na AWS: configure em Lambda > Configuration > Environment Variables
_VALID_KEY_HASH = os.environ.get("API_KEY_HASH", "")


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Valida a API Key recebida no header x-api-key.

    Comparação com hash SHA-256 para evitar timing attacks
    (nunca compare strings de segurança com == diretamente).

    Retorna (True, "") se válida, ou (False, motivo) se inválida.
    """
    if not api_key:
        return False, "Header x-api-key ausente ou vazio"

    if not _VALID_KEY_HASH:
        logger.error("API_KEY_HASH não configurada nas variáveis de ambiente")
        return False, "Serviço temporariamente indisponível"

    # Hash da chave recebida para comparação segura
    received_hash = hashlib.sha256(api_key.strip().encode()).hexdigest()

    # hmac.compare_digest evita timing attack
    if hmac.compare_digest(received_hash, _VALID_KEY_HASH):
        return True, ""

    return False, "API Key inválida"


def generate_key_hash(plain_key: str) -> str:
    """
    Utilitário para gerar o hash de uma API Key.
    Use isso localmente para gerar o valor que vai em API_KEY_HASH:

        python3 -c "from auth import generate_key_hash; print(generate_key_hash('minha-chave-secreta'))"
    """
    return hashlib.sha256(plain_key.encode()).hexdigest()