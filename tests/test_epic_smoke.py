import unittest
import json
import os
import tempfile

from vulnerability_analyzer import VulnerabilityAnalyzer
from vulnerability_security_automator import VulnerabilitySecurityAutomator
from vulnerability_predictor_pipeline import VulnerabilityPredictorPipeline
from vulnerability_security_optimizer import VulnerabilitySecurityOptimizer

class EpicPracticalVerificationTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_file_path = os.path.join(self.test_dir.name, "vulnerabilities_feed.json")
        
        # Создаем реалистичный файл с данными уязвимостей (телеметрия и тренды)
        realistic_data = [
            {"id": "CVE-2023-38606", "component": "kernel", "severity": "HIGH", "exploit_probability": 0.85, "vector": "LPE"},
            {"id": "CVE-2023-4911", "component": "glibc", "severity": "CRITICAL", "exploit_probability": 0.95, "vector": "Buffer Overflow"},
            {"id": "CVE-2024-21413", "component": "windows_mshtml", "severity": "HIGH", "exploit_probability": 0.78, "vector": "RCE"},
            {"id": "CVE-2024-3400", "component": "pan_os", "severity": "CRITICAL", "exploit_probability": 0.99, "vector": "Command Injection"},
            {"id": "CVE-2023-22515", "component": "confluence", "severity": "HIGH", "exploit_probability": 0.82, "vector": "Auth Bypass"}
        ]
        
        with open(self.data_file_path, "w", encoding="utf-8") as f:
            json.dump(realistic_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_vulnerability_prediction_and_optimization_pipeline(self):
        print("\n--- ЗАПУСК ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Предиктивная кибер-защита ---")
        
        # 1. Проверяем VulnerabilityAnalyzer на реальном файле данных
        print(f"[1] Чтение и анализ файла уязвимостей: {self.data_file_path}")
        analyzer = VulnerabilityAnalyzer(data_source=self.data_file_path)
        analysis_result = analyzer.analyze_trends()
        print(f" -> Результат анализа трендов: {analysis_result}")
        self.assertIsNotNone(analysis_result)

        # 2. Интеграция со шлюзом безопасности через VulnerabilitySecurityAutomator
        print("[2] Запуск автоматизатора безопасности (VulnerabilitySecurityAutomator)...")
        automator = VulnerabilitySecurityAutomator(analyzer=analyzer)
        security_status = automator.evaluate_and_lock()
        print(f" -> Статус автоматизированного контура: {security_status}")
        self.assertTrue(security_status.get("secured", True))

        # 3. Прогон через пайплайн прогнозирования VulnerabilityPredictorPipeline
        print("[3] Выполнение предиктивного пайплайна (VulnerabilityPredictorPipeline)...")
        pipeline = VulnerabilityPredictorPipeline(automator=automator)
        prediction_report = pipeline.run_pipeline()
        print(f" -> Отчет пайплайна прогнозирования:\n{json.dumps(prediction_report, indent=2)}")
        self.assertIn("predictions", prediction_report)

        # 4. Завершение оптимизацией защиты в VulnerabilitySecurityOptimizer
        print("[4] Финальная оптимизация правил защиты (VulnerabilitySecurityOptimizer)...")
        optimizer = VulnerabilitySecurityOptimizer(pipeline_report=prediction_report)
        optimization_result = optimizer.optimize_rules()
        print(f" -> Примененные оптимизации защиты: {optimization_result}")
        self.assertIsNotNone(optimization_result)
        print("--- ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ---")

if __name__ == "__main__":
    unittest.main()