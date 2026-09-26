import unittest
import uuid
import random
import os
from skills.market_portfolio_insider_exposure_report import MarketPortfolioInsiderExposureReporter, generate_insider_exposure_report
from skills.db_storage import db_storage
from skills.market_anomaly_detector import market_anomaly_detector
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub
from skills.market_portfolio_audit_log_exporter import market_portfolio_audit_log_exporter
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.extractor_tool_1790087207 import extractor_tool_1790087207

class IntegrationTestMarketPortfolioInsiderExposureReport(unittest.TestCase):
    def test_end_to_end_insider_exposure_report_flow(self):
        unique_report_id = str(uuid.uuid4())
        random_exposure_value = round(random.uniform(1000.0, 99999.0), 2)

        class RealTestDatabase:
            def fetch_exposure_data(self):
                return {unique_report_id: random_exposure_value}

        class RealTestExtractor:
            def extract_stream(self):
                return {"status": "extracted", "id": unique_report_id}

        class RealTestMonitor:
            def evaluate_risk(self):
                return {"risk_level": "nominal", "score": random.randint(1, 10)}

        class RealTestDetector:
            def detect_exposure_spikes(self):
                return {"anomaly_score": random.random(), "flagged": True, "uid": unique_report_id}

        class RealTestDispatcher:
            def dispatch_signal(self, msg):
                return f"dispatched_{msg}_{unique_report_id}"

        class RealTestComplianceHub:
            def verify_compliance(self):
                return {"compliant": True, "hash": unique_report_id}

        class RealTestLogExporter:
            def export(self):
                return f"exported_{unique_report_id}"

        payload = {
            'db_storage': RealTestDatabase(),
            'extractor_tool_1790087207': RealTestExtractor(),
            'market_portfolio_monitor': RealTestMonitor(),
            'market_anomaly_detector': RealTestDetector(),
            'market_portfolio_alert_dispatcher': RealTestDispatcher(),
            'market_portfolio_audit_compliance_hub': RealTestComplianceHub(),
            'market_portfolio_audit_log_exporter': RealTestLogExporter()
        }

        reporter = MarketPortfolioInsiderExposureReporter(payload)

        report_result = reporter.build_report()
        self.assertIn('exposure_metric', report_result)
        self.assertEqual(report_result['exposure_metric'], random_exposure_value)

        streams_result = reporter.process_exposure_streams()
        self.assertIsInstance(streams_result, list)
        self.assertTrue(len(streams_result) > 0)

        anomaly_section = reporter.compile_anomaly_section()
        self.assertEqual(anomaly_section.get('uid'), unique_report_id)
        self.assertTrue(anomaly_section.get('flagged'))

        alert_msg = f"alert_{unique_report_id}"
        dispatch_res = reporter.trigger_alerts(alert_msg)
        self.assertIn(unique_report_id, dispatch_res)

        audit_res = reporter.run_audit_check()
        self.assertEqual(audit_res.get('hash'), unique_report_id)
        self.assertTrue(audit_res.get('compliant'))

        functional_wrapper_result = generate_insider_exposure_report(payload)
        self.assertEqual(functional_wrapper_result['exposure_metric'], random_exposure_value)

if __name__ == '__main__':
    unittest.main()