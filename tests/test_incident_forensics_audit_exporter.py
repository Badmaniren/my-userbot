import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.incident_forensics_audit_exporter import IncidentForensicsAuditExporter

class TestIncidentForensicsAuditExporter(unittest.TestCase):

    def setUp(self):
        self.exporter = IncidentForensicsAuditExporter()

    def test_export_compliance_report_integrity(self):
        # Генерируем хаотичные входные данные
        incident_id = uuid.uuid4().hex
        audit_data = {
            "timestamp": random.randint(1000000000, 9999999999),
            "severity": random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
            "evidence_hash": uuid.uuid4().hex,
            "actor": "".join(random.choices(string.ascii_letters, k=10))
        }

        # Мокаем файловую систему через io.BytesIO
        mock_file = io.StringIO()

        with patch('builtins.open', return_value=mock_file):
            result = self.exporter.export_to_compliance_format(incident_id, audit_data)

            # Проверяем, что метод вернул путь или статус
            self.assertTrue(result.endswith(".json") or result.endswith(".audit"))

            # Проверяем, что данные были записаны корректно
            content = mock_file.getvalue()
            self.assertIn(incident_id, content)
            self.assertIn(audit_data["evidence_hash"], content)
            self.assertIn(audit_data["severity"], content)

    def test_audit_trail_aggregation_logic(self):
        # Генерируем случайный набор логов
        log_count = random.randint(5, 20)
        raw_logs = [f"LOG_{uuid.uuid4().hex}" for _ in range(log_count)]

        # Мокаем внешний сервис сбора аудита
        with patch('skills.incident_forensics_audit_exporter.incident_audit_trail_collector') as mock_collector:
            mock_collector.fetch_logs.return_value = raw_logs

            processed_data = self.exporter.aggregate_audit_trail(uuid.uuid4().hex)

            # Проверяем, что количество записей совпадает
            self.assertEqual(len(processed_data), log_count)
            # Проверяем, что данные не были подменены
            for log in raw_logs:
                self.assertIn(log, processed_data)

    def test_forensics_report_bridge_connectivity(self):
        # Генерируем случайный URL и токен
        target_url = f"https://{uuid.uuid4().hex}.compliance.internal/api/v1/report"
        auth_token = uuid.uuid4().hex

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"status": "accepted", "ref": uuid.uuid4().hex}
            mock_post.return_value = mock_response

            status = self.exporter.dispatch_to_compliance_bridge(target_url, auth_token, {"data": "payload"})

            # Проверяем, что запрос ушел с правильными параметрами
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], target_url)
            self.assertEqual(kwargs['headers']['Authorization'], f"Bearer {auth_token}")
            self.assertTrue(status)

    def test_data_sanitization_on_export(self):
        # Проверка на очистку данных от мусора
        dirty_key = f"key_{uuid.uuid4().hex}"
        raw_val = uuid.uuid4().hex
        dirty_value = f"<script>{raw_val}</script>"
        input_data = {dirty_key: dirty_value}

        sanitized = self.exporter.sanitize_audit_data(input_data)

        # Проверяем, что теги были удалены или экранированы
        self.assertNotIn("<script>", sanitized[dirty_key])
        self.assertIn(raw_val[:5], sanitized[dirty_key])

if __name__ == '__main__':
    unittest.main()