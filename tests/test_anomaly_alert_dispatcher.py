import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_alert_dispatcher import (
    AnomalyAlertDispatcher,
    AnomalyAlertDispatcherError,
    dispatch_alert
)

class TestAnomalyAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.random_endpoint = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.random_token = uuid.uuid4().hex
        self.random_timeout = random.randint(1, 30)
        self.dispatcher = AnomalyAlertDispatcher(
            endpoint=self.random_endpoint,
            api_token=self.random_token,
            timeout=self.random_timeout
        )

    def test_init_properties(self):
        self.assertEqual(self.dispatcher.endpoint, self.random_endpoint)
        self.assertEqual(self.dispatcher.api_token, self.random_token)
        self.assertEqual(self.dispatcher.timeout, self.random_timeout)

        dispatcher_no_token = AnomalyAlertDispatcher(endpoint=self.random_endpoint)
        self.assertIsNone(dispatcher_no_token.api_token)
        self.assertEqual(dispatcher_no_token.timeout, 5)

    def test_dispatch_alert_success(self):
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        message = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        telemetry_key = uuid.uuid4().hex
        telemetry_val = random.randint(100, 999)
        telemetry = {telemetry_key: telemetry_val}

        with patch('skills.anomaly_alert_dispatcher.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.dispatcher.dispatch_alert(severity, message, telemetry)

            self.assertTrue(result)
            mock_post.assert_called_once()
            
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], self.random_endpoint)
            self.assertEqual(kwargs['timeout'], self.random_timeout)
            self.assertEqual(kwargs['headers']['Authorization'], f"Bearer {self.random_token}")
            
            payload = kwargs['json']
            self.assertEqual(payload['severity'], severity)
            self.assertEqual(payload['message'], message)
            self.assertEqual(payload['telemetry'], telemetry)

    def test_dispatch_alert_no_endpoint_raises_error(self):
        dispatcher_invalid = AnomalyAlertDispatcher(endpoint="")
        severity = random.choice(["INFO", "WARNING"])
        message = uuid.uuid4().hex

        with self.assertRaises(AnomalyAlertDispatcherError) as ctx:
            dispatcher_invalid.dispatch_alert(severity, message)
        
        self.assertIn("Invalid endpoint", str(ctx.exception))

    def test_dispatch_alert_request_exception_raises_error(self):
        severity = random.choice(["ERROR", "FATAL"])
        message = uuid.uuid4().hex
        exception_msg = uuid.uuid4().hex

        with patch('skills.anomaly_alert_dispatcher.requests.post') as mock_post:
            mock_post.side_effect = Exception(exception_msg)

            with self.assertRaises(AnomalyAlertDispatcherError) as ctx:
                self.dispatcher.dispatch_alert(severity, message)
            
            self.assertIn("Failed to dispatch alert", str(ctx.exception))
            self.assertIn(exception_msg, str(ctx.exception))

    def test_dispatch_alert_integration_function_with_logger(self):
        dispatch_id = uuid.uuid4().hex
        target_service = f"service-{uuid.uuid4().hex[:8]}"
        
        anomaly_item = {
            "id": uuid.uuid4().hex,
            "metric": random.randint(1, 100)
        }

        audit_hub = MagicMock()
        audit_hub.logger.get_anomalies.return_value = [anomaly_item]

        result_payload = dispatch_alert(audit_hub, target_service, dispatch_id)

        self.assertEqual(result_payload["dispatch_id"], dispatch_id)
        self.assertEqual(result_payload["target_service"], target_service)
        self.assertEqual(result_payload["status"], "dispatched")
        self.assertEqual(result_payload["anomalies"], [anomaly_item])
        audit_hub.logger.get_anomalies.assert_called_once()

    def test_dispatch_alert_integration_function_direct_method(self):
        dispatch_id = uuid.uuid4().hex
        target_service = f"service-{uuid.uuid4().hex[:8]}"
        
        anomaly_item = {
            "error_code": random.randint(500, 599),
            "trace": uuid.uuid4().hex
        }

        audit_hub = MagicMock(spec=[])
        audit_hub.get_anomalies = MagicMock(return_value=[anomaly_item])

        result_payload = dispatch_alert(audit_hub, target_service, dispatch_id)

        self.assertEqual(result_payload["dispatch_id"], dispatch_id)
        self.assertEqual(result_payload["target_service"], target_service)
        self.assertEqual(result_payload["status"], "dispatched")
        self.assertEqual(result_payload["anomalies"], [anomaly_item])
        audit_hub.get_anomalies.assert_called_once()

    def test_dispatch_alert_integration_function_no_anomalies_source(self):
        dispatch_id = uuid.uuid4().hex
        target_service = f"service-{uuid.uuid4().hex[:8]}"

        audit_hub = MagicMock(spec=[])

        result_payload = dispatch_alert(audit_hub, target_service, dispatch_id)

        self.assertEqual(result_payload["dispatch_id"], dispatch_id)
        self.assertEqual(result_payload["target_service"], target_service)
        self.assertEqual(result_payload["status"], "dispatched")
        self.assertEqual(result_payload["anomalies"], [])

if __name__ == '__main__':
    unittest.main()