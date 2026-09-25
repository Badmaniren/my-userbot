import unittest
import uuid
import random
import os
from skills.market_anomaly_detector import market_anomaly_detector, MarketAnomalyDetector, detect_anomalies, dispatch_anomaly_alert, export_anomaly_audit

class RealStorage:
    def __init__(self, filepath):
        self.filepath = filepath
        self.saved_data = []

    def save_anomaly(self, data):
        self.saved_data.append(data)
        with open(self.filepath, "a") as f:
            f.write(str(data) + "\n")

class RealGateway:
    def __init__(self, data_to_return):
        self.data_to_return = data_to_return

    def fetch_market_data(self):
        return self.data_to_return

class RealDispatcher:
    def __init__(self):
        self.dispatched = []

    def send(self, payload):
        self.dispatched.append(payload)

class RealAuditExporter:
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def write_log(self, message):
        with open(self.log_filepath, "a") as f:
            f.write(message + "\n")

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, f"db_{uuid.uuid4().hex}.txt")
        self.log_path = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.log")

    def tearDown(self):
        for path in [self.db_path, self.log_path, self.test_dir]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    for f in os.listdir(path):
                        os.remove(os.path.join(path, f))
                    os.rmdir(path)
                else:
                    os.remove(path)

    def test_full_anomaly_detection_pipeline_integration(self):
        random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_threshold = random.uniform(1000.0, 500000.0)
        random_anomaly_id = str(uuid.uuid4())
        market_data_payload = {"market_status": "volatile", "id": random_anomaly_id, "rate": random.randint(1, 100)}

        storage = RealStorage(self.db_path)
        gateway = RealGateway(market_data_payload)
        dispatcher = RealDispatcher()
        audit_exporter = RealAuditExporter(self.log_path)

        detector_instance = market_anomaly_detector(db_storage=storage)

        analysis_result = detector_instance.analyze_ticker(random_ticker, random_threshold)
        self.assertTrue(analysis_result.get("anomaly_detected"))
        self.assertEqual(analysis_result.get("ticker"), random_ticker)

        self.assertTrue(os.path.exists(self.db_path))
        with open(self.db_path, "r") as f:
            content = f.read()
            self.assertIn(random_ticker, content)

        gateway_result = detect_anomalies(random_anomaly_id, gateway=gateway)
        self.assertEqual(gateway_result.get("id"), random_anomaly_id)
        self.assertEqual(gateway_result.get("market_status"), "volatile")

        import skills.market_anomaly_detector as mod
        mod.market_portfolio_alert_dispatcher = dispatcher
        mod.market_portfolio_audit_log_exporter = audit_exporter

        alert_payload = {"anomaly_id": random_anomaly_id, "ticker": random_ticker, "metric": random_threshold}
        dispatch_anomaly_alert(alert_payload)
        self.assertIn(alert_payload, dispatcher.dispatched)

        log_message = f"Audit log entry for {random_anomaly_id} on {random_ticker}"
        export_anomaly_audit(log_message)

        self.assertTrue(os.path.exists(self.log_path))
        with open(self.log_path, "r") as f:
            log_content = f.read()
            self.assertIn(log_message, log_content)

if __name__ == "__main__":
    unittest.main()