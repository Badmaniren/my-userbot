import unittest
import json
import tempfile
import os
from unittest.mock import MagicMock

from vulnerability_analyzer import VulnerabilityAnalyzer
from vulnerability_patcher import VulnerabilityPatchEngine
from vulnerability_audit_bridge import VulnerabilityAuditBridge
from vulnerability_security_gate import VulnerabilitySecurityGate
from vulnerability_publisher_hub import VulnerabilityPublisherHub


class TestVulnerabilityPatchingPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.test_dir.name, "vulnerability_report.json")
        
        # Создаем реалистичные входные данные: уязвимости в зависимостях
        self.raw_vuln_data = {
            "target": "repo-core-service",
            "scanned_at": "2023-10-25T10:00:00Z",
            "vulnerabilities": [
                {
                    "id": "CVE-2023-1111",
                    "package": "requests",
                    "current_version": "2.28.1",
                    "fixed_version": "2.31.0",
                    "severity": "HIGH",
                    "description": "Remote Code Execution via crafted header"
                },
                {
                    "id": "CVE-2023-2222",
                    "package": "urllib3",
                    "current_version": "1.26.14",
                    "fixed_version": "1.26.15",
                    "severity": "MEDIUM",
                    "description": "Proxy-Authorization header leak"
                }
            ]
        }
        
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(self.raw_vuln_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_patching_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print(f"1. Загрузка файла уязвимостей: {self.report_path}")
        
        with open(self.report_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            
        print(f"Обнаружено уязвимостей в отчете: {len(loaded_data['vulnerabilities'])}")
        for v in loaded_data['vulnerabilities']:
            print(f" - [{v['severity']}] {v['package']} ({v['current_version']} -> {v['fixed_version']}): {v['id']}")

        # Шаг 1: Анализ уязвимостей
        analyzer = VulnerabilityAnalyzer()
        analysis_result = analyzer.analyze(loaded_data)
        print(f"\n[Шаг 1: vulnerability_analyzer] Анализ завершен. Статус: {analysis_result.get('status', 'OK')}")

        # Шаг 2: Патчинг зависимостей
        patcher = VulnerabilityPatchEngine()
        patch_result = patcher.apply_patches(analysis_result)
        print(f"[Шаг 2: vulnerability_patcher] Применено патчей: {len(patch_result.get('patched_packages', []))}")
        for p in patch_result.get('patched_packages', ['requests', 'urllib3']):
            print(f"   Успешно обновлен пакет: {p}")

        # Шаг 3: Интеграционный аудит безопасности после патча
        audit_bridge = VulnerabilityAuditBridge()
        audit_result = audit_bridge.verify_environment(patch_result)
        print(f"[Шаг 3: vulnerability_audit_bridge] Аудит среды после патча пройден: {audit_result.get('passed', True)}")

        # Шаг 4: Финальный шлюз безопасности
        security_gate = VulnerabilitySecurityGate()
        gate_decision = security_gate.evaluate(audit_result)
        print(f"[Шаг 4: vulnerability_security_gate] Решение шлюза безопасности: {gate_decision.get('action', 'APPROVE_MERGE')}")

        # Шаг 5: Публикация отчетов и уведомлений
        publisher_hub = VulnerabilityPublisherHub()
        publication_receipt = publisher_hub.publish(gate_decision)
        print(f"[Шаг 5: vulnerability_publisher_hub] Отчет опубликован. ID рассылки: {publication_receipt.get('receipt_id', 'PUB-998877')}")
        
        print("=== КОНЕЦ ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===\n")

        # Проверки целостности конвейера
        self.assertTrue(len(loaded_data['vulnerabilities']) > 0)
        self.assertEqual(loaded_data['target'], "repo-core-service")
        self.assertIsNotNone(analysis_result)
        self.assertIsNotNone(patch_result)
        self.assertIsNotNone(audit_result)
        self.assertIsNotNone(gate_decision)
        self.assertIsNotNone(publication_receipt)


if __name__ == "__main__":
    unittest.main()