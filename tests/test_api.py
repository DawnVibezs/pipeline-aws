"""
Testes da Fase 3 — API Gateway (auth, rotas, respostas).
Execute com: python3 -m unittest tests/test_api.py -v
"""
import hashlib
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# boto3 só existe dentro da AWS — mockamos antes de qualquer import
boto3_mock = MagicMock()
sys.modules["boto3"]                      = boto3_mock
sys.modules["boto3.dynamodb"]             = MagicMock()
sys.modules["boto3.dynamodb.conditions"]  = MagicMock()
sys.modules["botocore"]                   = MagicMock()
sys.modules["botocore.exceptions"]        = MagicMock()


# ─── Auth ─────────────────────────────────────────────────────────────────────

class TestAuth(unittest.TestCase):

    def setUp(self):
        self.plain_key  = "minha-chave-secreta-123"
        self.valid_hash = hashlib.sha256(self.plain_key.encode()).hexdigest()

    def _get_auth(self, key_hash):
        with patch.dict(os.environ, {"API_KEY_HASH": key_hash}):
            # Reimporta o módulo para pegar o env atualizado
            import importlib
            import auth
            importlib.reload(auth)
            return auth

    def test_chave_valida(self):
        auth = self._get_auth(self.valid_hash)
        valid, msg = auth.validate_api_key(self.plain_key)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_chave_invalida(self):
        auth = self._get_auth(self.valid_hash)
        valid, msg = auth.validate_api_key("chave-errada")
        self.assertFalse(valid)
        self.assertIn("inválida", msg)

    def test_chave_vazia(self):
        auth = self._get_auth(self.valid_hash)
        valid, msg = auth.validate_api_key("")
        self.assertFalse(valid)
        self.assertIn("ausente", msg)

    def test_sem_env_configurada(self):
        auth = self._get_auth("")
        valid, msg = auth.validate_api_key("qualquer-chave")
        self.assertFalse(valid)

    def test_generate_key_hash_retorna_sha256(self):
        import auth
        result = auth.generate_key_hash("teste")
        self.assertEqual(len(result), 64)  # SHA-256 = 64 chars hex


# ─── Response ─────────────────────────────────────────────────────────────────

class TestResponse(unittest.TestCase):

    def setUp(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
        import response
        self.response = response

    def test_ok_retorna_200(self):
        resp = self.response.ok({"job_id": "abc"})
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["job_id"], "abc")

    def test_ok_status_customizado(self):
        resp = self.response.ok({}, status_code=201)
        self.assertEqual(resp["statusCode"], 201)

    def test_error_retorna_status_correto(self):
        resp = self.response.error(404, "Não encontrado")
        self.assertEqual(resp["statusCode"], 404)
        body = json.loads(resp["body"])
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["message"], "Não encontrado")

    def test_error_com_details(self):
        resp = self.response.error(400, "Inválido", details={"campo": "email"})
        body = json.loads(resp["body"])
        self.assertIn("details", body["error"])

    def test_headers_cors_presentes(self):
        resp = self.response.ok({})
        self.assertIn("Access-Control-Allow-Origin", resp["headers"])

    def test_meta_timestamp_presente(self):
        resp = self.response.ok({})
        body = json.loads(resp["body"])
        self.assertIn("timestamp", body["meta"])


# ─── Routes ───────────────────────────────────────────────────────────────────

class TestRoutes(unittest.TestCase):

    def _make_event(self, method, path, params=None):
        return {
            "httpMethod":            method,
            "path":                  path,
            "queryStringParameters": params,
        }

    @patch.dict(os.environ, {"DYNAMO_TABLE": "pipeline-jobs"})
    @patch("routes.get_job")
    def test_get_job_existente(self, mock_get):
        mock_get.return_value = {
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "SUCCESS",
        }
        import routes
        event  = self._make_event("GET", "/results/550e8400-e29b-41d4-a716-446655440000")
        resp   = routes.route_request("GET", "/results/550e8400-e29b-41d4-a716-446655440000", event)
        self.assertEqual(resp["statusCode"], 200)

    @patch.dict(os.environ, {"DYNAMO_TABLE": "pipeline-jobs"})
    @patch("routes.get_job")
    def test_get_job_nao_encontrado(self, mock_get):
        mock_get.return_value = None
        import routes
        event = self._make_event("GET", "/results/550e8400-e29b-41d4-a716-446655440000")
        resp  = routes.route_request("GET", "/results/550e8400-e29b-41d4-a716-446655440000", event)
        self.assertEqual(resp["statusCode"], 404)

    @patch.dict(os.environ, {"DYNAMO_TABLE": "pipeline-jobs"})
    def test_get_job_id_invalido(self):
        import routes
        event = self._make_event("GET", "/results/nao-e-uuid")
        resp  = routes.route_request("GET", "/results/nao-e-uuid", event)
        self.assertEqual(resp["statusCode"], 400)

    @patch.dict(os.environ, {"DYNAMO_TABLE": "pipeline-jobs"})
    @patch("routes.list_jobs")
    def test_list_jobs(self, mock_list):
        mock_list.return_value = ([{"job_id": "abc", "status": "SUCCESS"}], None)
        import routes
        event = self._make_event("GET", "/results", params={"limit": "10"})
        resp  = routes.route_request("GET", "/results", event)
        self.assertEqual(resp["statusCode"], 200)
        body  = json.loads(resp["body"])
        self.assertEqual(body["data"]["count"], 1)

    @patch.dict(os.environ, {"DYNAMO_TABLE": "pipeline-jobs"})
    @patch("routes.list_jobs")
    def test_list_jobs_status_invalido(self, mock_list):
        import routes
        event = self._make_event("GET", "/results", params={"status": "PENDENTE"})
        resp  = routes.route_request("GET", "/results", event)
        self.assertEqual(resp["statusCode"], 400)

    @patch.dict(os.environ, {"DYNAMO_TABLE": "pipeline-jobs"})
    def test_rota_inexistente(self):
        import routes
        event = self._make_event("POST", "/outro")
        resp  = routes.route_request("POST", "/outro", event)
        self.assertEqual(resp["statusCode"], 404)


if __name__ == "__main__":
    unittest.main()