import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_storage = {"status": "connected", "path": "/tmp/test_db"}
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=self.db_storage)

    def test_visualize_integration_flow(self):
        # Генерация случайных данных для исключения хардкода
        portfolio_id = str(uuid.uuid4())
        risk_score = round(random.uniform(0.1, 0.99), 4)
        tail_risk = {"var_95": random.uniform(0.01, 0.05), "cvar": random.uniform(0.02, 0.08)}

        payload = {
            "portfolio_id": portfolio_id,
            "adaptive_risk_score": risk_score,
            "tail_risk_metrics": tail_risk,
            "format": "graphical",
            "stream_payload": "stream_data_chunk_001"
        }

        # Вызов модуля без моков
        result = self.visualizer.visualize(payload)

        # Проверка целостности данных
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["adaptive_risk_score"], risk_score)
        self.assertEqual(result["tail_risk_metrics"], tail_risk)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")

    def test_text_summary_format_integrity(self):
        portfolio_id = str(uuid.uuid4())
        risk_score = random.randint(1, 100)

        payload = {
            "report_id": portfolio_id,
            "adaptive_risk_score": risk_score,
            "format": "text_summary",
            "export_to_text_report": True
        }

        result = self.visualizer.visualize(payload)

        # Проверка корректности формирования строки
        self.assertIn(portfolio_id, result)
        self.assertIn(str(risk_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_error_handling_invalid_payload(self):
        # Проверка обработки некорректного типа данных (античит-требование)
        invalid_payload = [1, 2, 3]
        result = self.visualizer.visualize(invalid_payload)
        
        self.assertEqual(result, str(invalid_payload))

    def test_empty_payload_resilience(self):
        # Проверка на пустой словарь
        result = self.visualizer.visualize({})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertIsNone(result.get("portfolio_id"))

if __name__ == "__main__":
    unittest.main()