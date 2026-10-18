import unittest
import os
import json
import uuid
import tempfile
import shutil
from skills.audit_export_bridge import AuditExportBridge
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter

class TestAuditExportBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        self.log_path = os.path.join(self.test_dir, "audit.log")
        self.export_path = os.path.join(self.test_dir, "report.json")
        os.makedirs(self.repo_path)

        self.hub = AnomalyAuditHub(self.repo_path, self.log_path, threshold=0.5)
        self.exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        self.bridge = AuditExportBridge(self.hub, self.exporter)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_bridge_data_integrity_flow(self):
        # Генерируем случайные данные для проверки
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = float(uuid.uuid4().int % 100)
        source = f"source_{uuid.uuid4().hex[:4]}"

        # 1. Заполняем хаб данными
        self.hub.log_anomaly(source, "CRITICAL", "Test anomaly", {"cpu": 99})
        self.hub.aggregate_and_report(metric_name, metric_value)

        # 2. Выполняем интеграционный переход через мост
        # Предполагаем, что bridge имеет метод transfer, который берет данные из hub и отдает в exporter
        result_path = self.bridge.transfer_to_json(self.export_path)

        # 3. Проверка целостности
        self.assertTrue(os.path.exists(result_path), "Файл отчета не был создан")

        with open(result_path, 'r') as f:
            data = json.load(f)

        # Проверяем, что данные из хаба попали в экспорт
        found = False
        for entry in data:
            if entry.get("metric_name") == metric_name and entry.get("value") == metric_value:
                found = True
                break

        self.assertTrue(found, "Данные не прошли через мост или были искажены")

    def test_bridge_empty_state_handling(self):
        # Проверка поведения при пустом хабе
        empty_export_path = os.path.join(self.test_dir, "empty.json")

        # Мост должен корректно обработать отсутствие данных без падения
        result_path = self.bridge.transfer_to_json(empty_export_path)

        self.assertTrue(os.path.exists(result_path))
        with open(result_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 0, "Экспорт должен быть пустым")

if __name__ == '__main__':
    unittest.main()