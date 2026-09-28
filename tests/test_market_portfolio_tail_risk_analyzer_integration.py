import unittest
import uuid
import random
from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer, market_portfolio_tail_risk_analyzer

class RealDatabaseStorageStub:
    def __init__(self):
        self.storage = {}

    def save_metric(self, metric_id, metrics):
        self.storage[metric_id] = metrics

class RealExtractorStub:
    def __init__(self, data):
        self.data = data

    def extract(self, portfolio_id):
        return self.data

class RealAnomalyDetectorStub:
    def detect(self, asset_symbol):
        return {
            'signature': f"sig_{asset_symbol}_{uuid.uuid4().hex[:6]}",
            'asset': asset_symbol,
            'is_tail_risk_event': True
        }

class TestMarketPortfolioTailRiskAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.db = RealDatabaseStorageStub()
        self.rand_val = random.uniform(0.01, 0.05)
        self.extractor = RealExtractorStub([ -0.05, -0.04, -0.03, -0.02, 0.01, 0.02, 0.03 ])
        self.anomaly_detector = RealAnomalyDetectorStub()

        self.analyzer = MarketPortfolioTailRiskAnalyzer(
            db_storage=self.db,
            extractor_tool_1790087207=self.extractor,
            market_anomaly_detector=self.anomaly_detector
        )

    def test_integration_tail_risk_workflow(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        confidence = round(random.uniform(0.90, 0.99), 2)

        result = self.analyzer.calculate_tail_risk(portfolio_id, confidence_level=confidence)

        self.assertIn("var", result)
        self.assertIn("cvar", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertLessEqual(result["var"], 0.0)
        self.assertLessEqual(result["cvar"], result["var"])

    def test_integration_persistence_and_anomaly(self):
        metric_id = f"metric_{uuid.uuid4().hex}"
        persisted_id = self.analyzer.persist_tail_risk_metrics(metric_id)

        self.assertEqual(metric_id, persisted_id)
        self.assertIn(metric_id, self.db.storage)

        saved_metrics = self.db.storage[metric_id]
        self.assertIn("var", saved_metrics)
        self.assertIn("cvar", saved_metrics)

        asset_symbol = f"ASSET_{uuid.uuid4().hex[:4].upper()}"
        anomaly_eval = self.analyzer.evaluate_anomaly_impact(asset_symbol)

        self.assertEqual(anomaly_eval['asset'], asset_symbol)
        self.assertTrue(anomaly_eval['mitigation_required'])
        self.assertIn(asset_symbol, anomaly_eval['anomaly_signature'])

    def test_integration_robust_extraction_and_shock(self):
        portfolio_id = f"stream_{uuid.uuid4().hex}"
        extracted_data = self.analyzer.robust_data_extraction(portfolio_id)

        self.assertIsNotNone(extracted_data)
        self.assertEqual(len(extracted_data), 7)

        vector_size = random.randint(3, 10)
        portfolio_vector = [random.uniform(10.0, 100.0) for _ in range(vector_size)]
        shock_magnitude = random.uniform(5.0, 25.0)

        shocked_vector = self.analyzer.simulate_extreme_shock(portfolio_vector, shock_magnitude)
        self.assertEqual(len(shocked_vector), vector_size)
        for original, shocked in zip(portfolio_vector, shocked_vector):
            self.assertLess(shocked, original)

    def test_global_functional_wrapper(self):
        portfolio_id = f"func_{uuid.uuid4().hex}"
        res = market_portfolio_tail_risk_analyzer(portfolio_id, confidence_level=0.95)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), portfolio_id)
        self.assertIn("var", res)
        self.assertIn("cvar", res)

if __name__ == '__main__':
    unittest.main()