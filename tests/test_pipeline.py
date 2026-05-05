"""
Testes unitários do pipeline.
Execute com: pytest tests/ -v
"""
import json
import unittest
from validator import validate_records
from utils import detect_file_type, build_job_result

# ─── Processor ────────────────────────────────────────────────────────────────

from processor import process_file


class TestProcessor(unittest.TestCase):

    def test_parse_csv_basico(self):
        csv_content = "id,name,email\n1,Ana Silva,ana@email.com\n2,João Costa,joao@email.com"
        records = process_file(csv_content, "csv")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["name"], "Ana Silva")

    def test_parse_csv_ignora_linhas_vazias(self):
        csv_content = "id,name,email\n1,Ana,ana@email.com\n,,\n2,João,joao@email.com"
        records = process_file(csv_content, "csv")
        self.assertEqual(len(records), 2)

    def test_parse_csv_normaliza_headers(self):
        csv_content = "  ID , Name , Email \n1,Ana,ana@email.com"
        records = process_file(csv_content, "csv")
        self.assertIn("id", records[0])
        self.assertIn("name", records[0])

    def test_parse_json_array(self):
        json_content = json.dumps([
            {"id": "1", "name": "Ana", "email": "ana@email.com"}
        ])
        records = process_file(json_content, "json")
        self.assertEqual(len(records), 1)

    def test_parse_json_com_chave_data(self):
        json_content = json.dumps({
            "data": [{"id": "1", "name": "Ana", "email": "ana@email.com"}]
        })
        records = process_file(json_content, "json")
        self.assertEqual(len(records), 1)

    def test_tipo_invalido_lanca_erro(self):
        with self.assertRaises(ValueError):
            process_file("conteudo", "xml")


# ─── Validator ────────────────────────────────────────────────────────────────



class TestValidator(unittest.TestCase):

    def _record(self, **kwargs):
        base = {"id": "1", "name": "Ana Silva", "email": "ana@email.com"}
        base.update(kwargs)
        return base

    def test_registro_valido(self):
        valid, errors = validate_records([self._record()])
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(errors), 0)

    def test_campo_obrigatorio_ausente(self):
        record = {"id": "1", "name": "Ana"}  # sem email
        valid, errors = validate_records([record])
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("email", errors[0]["errors"][0])

    def test_email_invalido(self):
        valid, errors = validate_records([self._record(email="nao-e-email")])
        self.assertEqual(len(errors), 1)

    def test_transformacao_normaliza_email(self):
        valid, _ = validate_records([self._record(email="ANA@EMAIL.COM")])
        self.assertEqual(valid[0]["email"], "ana@email.com")

    def test_transformacao_title_case_nome(self):
        valid, _ = validate_records([self._record(name="ana silva")])
        self.assertEqual(valid[0]["name"], "Ana Silva")

    def test_campo_vazio_falha(self):
        valid, errors = validate_records([self._record(name="")])
        self.assertEqual(len(errors), 1)

    def test_multiplos_registros_misturados(self):
        records = [
            self._record(id="1"),
            {"id": "2", "name": "Sem email"},         # inválido
            self._record(id="3", email="invalido"),   # inválido
        ]
        valid, errors = validate_records(records)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(errors), 2)


# ─── Utils ────────────────────────────────────────────────────────────────────


class TestUtils(unittest.TestCase):

    def test_detecta_csv(self):
        self.assertEqual(detect_file_type("raw/dados.csv"), "csv")

    def test_detecta_json(self):
        self.assertEqual(detect_file_type("raw/dados.json"), "json")

    def test_extensao_invalida(self):
        with self.assertRaises(ValueError):
            detect_file_type("raw/dados.xlsx")

    def test_build_job_result_success(self):
        result = build_job_result(
            job_id="abc-123",
            source_file="raw/teste.csv",
            status="SUCCESS",
            total=10,
            valid=9,
            error_count=1,
            output_key="processed/abc-123.json",
            started_at="2024-01-01T00:00:00",
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["valid_records"], 9)
        self.assertIn("ttl", result)  # TTL deve estar presente

    def test_build_job_result_failed_tem_error_message(self):
        result = build_job_result(
            job_id="abc-123",
            source_file="raw/teste.csv",
            status="FAILED",
            total=0,
            valid=0,
            error_count=1,
            output_key="errors/abc-123.txt",
            started_at="2024-01-01T00:00:00",
            error_message="Arquivo corrompido",
        )
        self.assertIn("error_message", result)
        self.assertEqual(result["error_message"], "Arquivo corrompido")


if __name__ == "__main__":
    unittest.main()