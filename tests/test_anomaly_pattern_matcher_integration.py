import unittest
import uuid
import random
import os
from skills.anomaly_pattern_matcher import AnomalyPatternMatcher, PatternDefinition, match_pattern
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyPatternMatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.log_path = f"test_anomaly_log_{uuid.uuid4()}.json"
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.logger.clear_logs()

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_pattern_matching_integration_flow(self):
        random_suffix = str(uuid.uuid4())[:8]
        custom_pattern_id = f"custom-err-{random_suffix}"
        log_line = f"ERROR {random_suffix}: CRITICAL_DATABASE_TIMEOUT occurred during transaction"

        matcher = AnomalyPatternMatcher()
        pattern = PatternDefinition(
            pattern_id=custom_pattern_id,
            regex="CRITICAL_DATABASE_TIMEOUT",
            severity="HIGH",
            category="DATABASE"
        )
        matcher.add_pattern(pattern)

        matches = matcher.match_log(log_line)
        self.assertTrue(len(matches) > 0, "Паттерн должен был совпасть с логом")

        matched_info = matches[0]
        self.assertEqual(matched_info["pattern_id"], custom_pattern_id)
        self.assertEqual(matched_info["severity"], "HIGH")
        self.assertEqual(matched_info["category"], "DATABASE")

        self.logger.log_anomaly(
            source="anomaly_pattern_matcher",
            severity=matched_info["severity"],
            details=f"Matched pattern {matched_info['pattern_id']} in line: {log_line}",
            telemetry_snapshot={"random_metric": random.randint(100, 999)}
        )

        anomalies = self.logger.get_anomalies()
        self.assertEqual(len(anomalies), 1, "Аномалия должна быть записана в лог-файл")
        self.assertEqual(anomalies[0]["source"], "anomaly_pattern_matcher")
        self.assertIn(custom_pattern_id, anomalies[0]["details"])

    def test_global_match_pattern_fallback(self):
        random_code = f"ERR-{random.randint(1000, 9999)}"
        log_line = f"System warning: timeout detected with code {random_code}"

        result = match_pattern(log_line)
        self.assertIsNotNone(result, "Функция match_pattern должна вернуть результат")
        self.assertIn("pattern", result)

        pattern_data = result["pattern"]
        self.assertEqual(pattern_data["pattern_id"], "fallback-pattern-id")
        self.assertEqual(pattern_data["severity"], "CRITICAL")
        self.assertEqual(pattern_data["matched_line"], log_line)

        self.logger.log_anomaly(
            source="global_matcher",
            severity=pattern_data["severity"],
            details=pattern_data["matched_line"],
            telemetry_snapshot={"code": random_code}
        )

        report = self.logger.get_structured_report()
        self.assertGreater(len(report), 0, "Структурированный отчет не должен быть пустым")
        self.assertTrue(os.path.exists(self.log_path), "Файл логов должен реально существовать на диске")

if __name__ == "__main__":
    unittest.main()