import unittest
import os
import json
import tempfile
from unittest.mock import patch

from vulnerability_analyzer import VulnerabilityAnalyzer
from vulnerability_security_automator import VulnerabilitySecurityAutomator
from vulnerability_predictor_pipeline import VulnerabilityPredictorPipeline
from vulnerability_security_optimizer import VulnerabilitySecurityOptimizer

class TestVulnerabilityCyberDefenseEpic(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.telemetry_path = os.path.join(self.test_dir.name, "vulnerability_telemetry.json")
        
        # Создаем реалистичный файл телеметрии уязвимостей и логов безопасности (20+ строк)
        realistic_telemetry = [
            {"id": "CVE-2024-1001", "component": "auth_service", "severity": "HIGH", "trend_score": 0.85, "vector": "network", "exploit_available": True},
            {"id": "CVE-2024-1002", "component": "payment_gateway", "severity": "CRITICAL", "trend_score": 0.95, "vector": "remote", "exploit_available": True},
            {"id": "CVE-2024-1003", "component": "user_profile", "severity": "MEDIUM", "trend_score": 0.45, "vector": "local", "exploit_available": False},
            {"id": "CVE-2024-1004", "component": "logger_module", "severity": "LOW", "trend_score": 0.20, "vector": "local", "exploit_available": False},
            {"id": "CVE-2024-1005", "component": "api_gateway", "severity": "HIGH", "trend_score": 0.88, "vector": "network", "exploit_available": True},
            {"id": "CVE-2024-1006", "component": "database_connector", "severity": "CRITICAL", "trend_score": 0.92, "vector": "remote", "exploit_available": True},
            {"id": "CVE-2024-1007", "component": "session_manager", "severity": "MEDIUM", "trend_score": 0.60, "vector": "network", "exploit_available": False},
            {"id": "CVE-2024-1008", "component": "cache_service", "severity": "LOW", "trend_score": 0.15, "vector": "local", "exploit_available": False},
            {"id": "CVE-2024-1009", "component": "notification_service", "severity": "MEDIUM", "trend_score": 0.50, "vector": "network", "exploit_available": False},
            {"id": "CVE-2024-1010", "component": "admin_panel", "severity": "CRITICAL", "trend_score": 0.99, "vector": "remote", "exploit_available": True},
            {"id": "CVE-2024-1011", "component": "file_uploader", "severity": "HIGH", "trend_score": 0.82, "vector": "network", "exploit_available": True},
            {"id": "CVE-2024-1012", "component": "config_parser", "severity": "MEDIUM", "trend_score": 0.55, "vector": "local", "exploit_available": False},
            {"id": "CVE-2024-1013", "component": "crypto_lib", "severity": "HIGH", "trend_score": 0.78, "vector": "remote", "exploit_available": True},
            {"id": "CVE-2024-1014", "component": "metrics_exporter", "severity": "LOW", "trend_score": 0.10, "vector": "network", "exploit_available": False},
            {"id": "CVE-2024-1015", "component": "search_engine", "severity": "MEDIUM", "trend_score": 0.65, "vector": "remote", "exploit_available": False},
            {"id": "CVE-2024-1016", "component": "plugin_loader", "severity": "CRITICAL", "trend_score": 0.97, "vector": "remote", "exploit_available": True},
            {"id": "CVE-2024-1017", "component": "websocket_handler", "severity": "HIGH", "trend_score": 0.80, "vector": "network", "exploit_available": True},
            {"id": "CVE-2024-1018", "component": "template_engine", "severity": "MEDIUM", "trend_score": 0.52, "vector": "local", "exploit_available": False},
            {"id": "CVE-2024-1019", "component": "dns_resolver", "severity": "LOW", "trend_score": 0.25, "vector": "network", "exploit_available": False},
            {"id": "CVE-2024-1020", "component": "proxy_module", "severity": "HIGH", "trend_score": 0.89, "vector": "network", "exploit_available": True}
        ]
        
        with open(self.telemetry_path, 'w', encoding='utf-8') as f:
            json.dump(realistic_telemetry, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_vulnerability_cyber_defense_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Продвинутая система прогнозирования уязвимостей и кибер-защиты ===")
        
        # 1. Шаг анализатора трендов уязвимостей
        analyzer = VulnerabilityAnalyzer()
        analysis_result = analyzer.analyze(self.telemetry_path)
        print(f"[1] VulnerabilityAnalyzer результаты анализа: {analysis_result}")
        self.assertIsNotNone(analysis_result)

        # 2. Шаг шлюза безопасности и автоматизатора
        automator = VulnerabilitySecurityAutomator()
        automator_result = automator.automate(analysis_result)
        print(f"[2] VulnerabilitySecurityAutomator контур защиты: {automator_result}")
        self.assertIsNotNone(automator_result)

        # 3. Шаг единого пайплайна прогнозирования
        pipeline = VulnerabilityPredictorPipeline()
        pipeline_forecast = pipeline.run(self.telemetry_path)
        print(f"[3] VulnerabilityPredictorPipeline прогноз: {pipeline_forecast}")
        self.assertIsNotNone(pipeline_forecast)

        # 4. Шаг оптимизатора защиты на основе предсказаний (завершение эпика)
        optimizer = VulnerabilitySecurityOptimizer()
        optimization_report = optimizer.optimize(pipeline_forecast)
        print(f"[4] VulnerabilitySecurityOptimizer отчет об оптимизации: {optimization_report}")
        self.assertIsNotNone(optimization_report)
        
        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == '__main__':
    unittest.main()