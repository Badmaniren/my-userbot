import unittest
import os
import uuid
import json
import random
import tempfile
from skills.incident_forensics_audit_exporter import incident_forensics_audit_exporter
from skills.incident_audit_trail_collector import incident_audit_trail_collector
from skills.incident_forensics_synthesizer import incident_forensics_synthesizer

class TestIncidentForensicsAuditExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.incident_id = str(uuid.uuid4())
        self.audit_data = {
            "incident_id": self.incident_id,
            "timestamp": random.randint(1600000000, 1700000000),
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "evidence_hash": str(uuid.uuid4()),
            "actor": "system_automated_audit"
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_forensics_export_pipeline(self):
        # 1. Сбор данных через реальный коллектор
        collector = incident_audit_trail_collector()
        raw_trail = collector.collect(self.incident_id)

        # 2. Синтез данных через реальный синтезатор
        synthesizer = incident_forensics_synthesizer()
        synthesized_report = synthesizer.synthesize(raw_trail, self.audit_data)

        # 3. Экспорт через тестируемый модуль
        exporter = incident_forensics_audit_exporter()
        export_path = os.path.join(self.test_dir.name, f"report_{self.incident_id}.json")

        result = exporter.export(synthesized_report, export_path)

        # Проверки
        self.assertTrue(os.path.exists(export_path), "Файл отчета не был создан на диске")
        self.assertTrue(result, "Модуль экспорта вернул False")

        with open(export_path, 'r') as f:
            exported_data = json.load(f)

        self.assertEqual(exported_data['incident_id'], self.incident_id, "ID инцидента в файле не совпадает с исходным")
        self.assertEqual(exported_data['evidence_hash'], self.audit_data['evidence_hash'], "Хэш доказательств поврежден при экспорте")

    def test_export_integrity_with_random_payloads(self):
        # Тест на устойчивость к случайным данным
        exporter = incident_forensics_audit_exporter()
        random_payload = {
            "id": str(uuid.uuid4()),
            "metrics": [random.random() for _ in range(5)],
            "status": "COMPLIANCE_READY"
        }

        target_file = os.path.join(self.test_dir.name, f"audit_{random.randint(1000, 9999)}.json")
        exporter.export(random_payload, target_file)

        self.assertTrue(os.path.getsize(target_file) > 0, "Экспортированный файл пуст")

        with open(target_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['id'], random_payload['id'])

if __name__ == '__main__':
    unittest.main()