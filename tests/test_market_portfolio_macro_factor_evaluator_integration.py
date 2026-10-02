import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_macro_factor_evaluator import MacroFactorEvaluator
from skills.db_storage import DBStorage
from skills.market_portfolio_collector_agent import PortfolioCollectorAgent
from skills.extractor_tool_1790087207 import MacroDataExtractor
import skills.market_anomaly_detector as market_anomaly_detector

class TestMacroFactorEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.collector = PortfolioCollectorAgent()
        self.extractor = MacroDataExtractor()
        self.evaluator = MacroFactorEvaluator(
            db_storage=self.db,
            collector=self.collector,
            extractor=self.extractor
        )
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"

    def test_evaluate_and_persist_integration(self):
        random_inflation = round(random.uniform(0.01, 0.15), 4)
        random_interest = round(random.uniform(0.01, 0.10), 4)

        expected_impact = (random_inflation * 0.5) + (random_interest * 0.3)

        result = self.evaluator.evaluate(self.portfolio_id)

        self.assertIn('portfolio_id', result)
        self.assertIn('report_id', result)
        self.assertIn('impact_score', result)
        self.assertEqual(result['portfolio_id'], self.portfolio_id)

        report_id = result['report_id']
        self.assertTrue(isinstance(report_id, str))
        self.assertTrue(len(report_id) > 0)

        report_path = f"reports/macro_{self.portfolio_id}.json"
        self.assertTrue(os.path.exists(report_path), "Файл отчета не был создан на диске")

        with open(report_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
            self.assertEqual(file_data['portfolio_id'], self.portfolio_id)
            self.assertEqual(file_data['report_id'], report_id)

        threshold = round(random.uniform(0.01, 0.05), 4)
        anomaly_result = self.evaluator.check_macro_anomalies(self.portfolio_id, threshold)
        self.assertIsNotNone(anomaly_result)

        new_score = round(random.uniform(1.0, 100.0), 2)
        try:
            self.evaluator.persist_evaluation(report_id, new_score)
        except Exception as e:
            self.fail(f"Метод persist_evaluation вызвал исключение: {e}")

    def tearDown(self):
        report_path = f"reports/macro_{self.portfolio_id}.json"
        if os.path.exists(report_path):
            try:
                os.remove(report_path)
            except OSError:
                pass

if __name__ == '__main__':
    unittest.main()