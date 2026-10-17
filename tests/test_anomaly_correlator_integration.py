import unittest
import uuid
import random
from skills.anomaly_correlator import AnomalyCorrelator
from skills.anomaly_filter import AnomalyFilter


class TestAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.correlator = AnomalyCorrelator()
        self.filter_module = AnomalyFilter()

    def test_correlate_metric_and_filter_integration(self):
        metric_name = f"metric_cpu_load_{uuid.uuid4().hex[:8]}"
        raw_value = round(random.uniform(90.0, 150.0), 2)

        is_anomaly = self.correlator.correlate_metric(metric_name, raw_value)
        self.assertTrue(is_anomaly, "Значение должно детектироваться как аномалия.")

        raw_data = {
            "source": metric_name,
            "severity": "HIGH",
            "details": f"Anomaly value {raw_value}",
            "telemetry_snapshot": {"value": raw_value, "status": "anomaly_detected"}
        }
        filtered_result = self.filter_module.filter(raw_data)
        self.assertIsNotNone(filtered_result, "Фильтр не должен возвращать None для аномальных данных.")

        report_data = self.correlator.correlate_events()
        self.assertIn("correlated_count", report_data)
        self.assertGreaterEqual(report_data["correlated_count"], 1)

    def test_analyze_execution_flow_integration(self):
        execution_id = f"exec_{uuid.uuid4().hex}"
        metric_key = f"memory_leak_{uuid.uuid4().hex[:6]}"
        metrics_payload = {
            metric_key: round(random.uniform(500.0, 2000.0), 2)
        }

        analysis_result = self.correlator.analyze_execution_flow(execution_id, metrics_payload)
        self.assertIsInstance(analysis_result, dict, "Результат анализа выполнения должен быть словарем.")
        
        report = self.correlator.get_correlation_report()
        self.assertIsNotNone(report, "Отчет корреляции не должен быть пустым.")


if __name__ == "__main__":
    unittest.main()