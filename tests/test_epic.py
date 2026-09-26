import unittest
import json
import os

from skills.epic import (
    market_portfolio_monitor,
    market_insider_activity_tracker,
    market_anomaly_detector,
    market_insider_alert_pipeline,
    market_portfolio_audit_compliance_hub,
    MarketParser,
    MarketReportGenerator,
    MarketInsiderActivityTrackerModuleAPI,
    MarketAnomalyDetector,
    MarketInsiderAlertPipeline,
    MarketPortfolioAuditComplianceHub
)

class TestEpicModule(unittest.TestCase):

    def test_epic_exports_and_functionality(self):
        sample_data = [
            {"ticker": "AAPL", "volume": 100000, "price": 150.0, "insider_flag": True},
            {"ticker": "GOOG", "volume": 20000, "price": 2800.0, "insider_flag": False}
        ]

        monitor_res = market_portfolio_monitor(sample_data)
        self.assertIsInstance(monitor_res, dict)
        self.assertEqual(monitor_res.get("processed"), 2)

        tracker_res = market_insider_activity_tracker(sample_data)
        self.assertIsInstance(tracker_res, list)
        self.assertEqual(len(tracker_res), 2)

        anomaly_res = market_anomaly_detector(sample_data)
        self.assertIsInstance(anomaly_res, list)
        self.assertEqual(len(anomaly_res), 2)

        pipeline_res = market_insider_alert_pipeline(sample_data)
        self.assertIsInstance(pipeline_res, list)
        self.assertEqual(len(pipeline_res), 2)

        compliance_res = market_portfolio_audit_compliance_hub()
        self.assertIsNotNone(compliance_res)

    def test_epic_class_instantiations(self):
        parser = MarketParser("test.json")
        self.assertIsNotNone(parser)

        generator = MarketReportGenerator("test.json")
        self.assertIsNotNone(generator)

        tracker_api = MarketInsiderActivityTrackerModuleAPI()
        self.assertIsNotNone(tracker_api)

        detector = MarketAnomalyDetector()
        self.assertIsNotNone(detector)

        pipeline = MarketInsiderAlertPipeline()
        self.assertIsNotNone(pipeline)

        hub = MarketPortfolioAuditComplianceHub()
        self.assertIsNotNone(hub)

if __name__ == '__main__':
    unittest.main()
