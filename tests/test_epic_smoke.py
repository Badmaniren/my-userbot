import unittest
import json
import os
import tempfile
from unittest.mock import patch

from vulnerability_analyzer import VulnerabilityAnalyzer
from vulnerability_patcher import VulnerabilityPatchEngine
from vulnerability_audit_bridge import VulnerabilityAuditBridge
from vulnerability_security_gate import VulnerabilitySecurityGate
from vulnerability_publisher_hub import VulnerabilityPublisherHub


class TestVulnerabilityPatchingPipelineRealExecution(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.vuln_db_path = os.path.join(self.test_dir.name, "vulnerabilities.json")
        self.audit_log_path = os.path.join(self.test_dir.name, "audit_results.json")
        self.report_path = os.path.join(self.test_dir.name, "security_report.json")

        self.raw_vulnerability_data = {
            "target_repo": "ung-core-service",
            "scan_timestamp": "2023-10-25T10:00:00Z",
            "vulnerabilities": [
                {
                    "id": "CVE-2023-38545",
                    "package": "curl",
                    "current_version": "7.88.0",
                    "fixed_version": "7.88.1",
                    "severity": "CRITICAL",
                    "description": "Heap-based buffer overflow in SOCKS5 proxy handshake"
                },
                {
                    "id": "CVE-2023-44487",
                    "package": "hyper",
                    "current_version": "0.14.26",
                    "fixed_version": "0.14.28",
                    "severity": "HIGH",
                    "description": "HTTP/2 Rapid Reset Attack"
                }
            ]
        }

        with open(self.vuln_db_path, "w", encoding="utf-8") as f:
            json.dump(self.raw_vulnerability_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_complete_vulnerability_patching_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: КОНВЕЙЕР ПАТЧИНГА УЯЗВИМОСТЕЙ ===")
        
        # Шаг 1: Анализ уязвимостей
        analyzer = VulnerabilityAnalyzer(vulnerability_source=self.vuln_db_path)
        analyzed_report = analyzer.run_analysis()
        
        print(f"[1] Анализ завершен. Обнаружено уязвимостей: {len(analyzed_report['vulnerabilities'])}")
        for vuln in analyzed_report['vulnerabilities']:
            print(f"    - [{vuln['severity']}] {vuln['id']}: пакет {vuln['package']} ({vuln['current_version']} -> {vuln['fixed_version']})")
        
        self.assertGreater(len(analyzed_report['vulnerabilities']), 0, "Анализатор должен найти уязвимости")

        # Шаг 2: Автоматический патчинг зависимостей
        patcher = VulnerabilityPatchEngine()
        patch_result = patcher.apply_patches(analyzed_report)
        
        print(f"[2] Патчинг зависимостей выполнен. Статус: {patch_result['status']}")
        print(f"    - Успешно пропатчено пакетов: {len(patch_result['patched_packages'])}")
        self.assertEqual(patch_result['status'], "SUCCESS", "Патчинг должен завершиться успешно")

        # Шаг 3: Интеграционная проверка безопасности после патчинга
        audit_bridge = VulnerabilityAuditBridge(output_path=self.audit_log_path)
        audit_result = audit_bridge.verify_patched_state(patch_result)
        
        print(f"[3] Интеграционный аудит пройден. Ошибок безопасности после патча: {audit_result['remaining_vulnerabilities_count']}")
        print(f"    - Лог аудита сохранен в: {self.audit_log_path}")
        self.assertEqual(audit_result['remaining_vulnerabilities_count'], 0, "После патчинга не должно остаться целевых уязвимостей")

        # Шаг 4: Финальный шлюз безопасности
        security_gate = VulnerabilitySecurityGate(threshold="HIGH")
        gate_decision = security_gate.evaluate(audit_result)
        
        print(f"[4] Шлюз безопасности (Security Gate): {'ПРОЙДЕН' if gate_decision['passed'] else 'ЗАБЛОКИРОВАН'}")
        print(f"    - Уровень риска: {gate_decision['risk_level']}")
        self.assertTrue(gate_decision['passed'], "Шлюз безопасности должен пропустить репозиторий после устранения уязвимостей")

        # Шаг 5: Публикация отчетов и оповещений
        publisher = VulnerabilityPublisherHub(report_destination=self.report_path)
        publish_result = publisher.publish(gate_decision, patch_result)
        
        print(f"[5] Конвейер публикации отчетов завершен.")
        print(f"    - Отчет опубликован по пути: {publish_result['destination']}")
        print(f"    - Уведомления отправлены в каналы интеграции: {publish_result['notifications_sent']}")

        self.assertTrue(os.path.exists(self.report_path), "Файл финального отчета должен быть создан")
        
        with open(self.report_path, "r", encoding="utf-8") as rf:
            saved_report = json.load(rf)
            print(f"    - Проверка содержимого файла отчета: статус конвейера = {saved_report.get('pipeline_status')}")
            self.assertEqual(saved_report.get('pipeline_status'), "COMPLETED")

        print("=== КОНЕЦ ПРАКТИЧЕСКОЙ ПРОВЕРКИ: ВСЕ МОДУЛИ ОТРАБОТАЛИ НА РЕАЛЬНЫХ ДАННЫХ ===\n")


if __name__ == "__main__":
    unittest.main()