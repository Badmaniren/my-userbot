import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import requests

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

    def test_dispatch_alert_success(self):
        random_severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        random_message = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        random_telemetry_key = uuid.uuid4().hex
        random_telemetry_val = random.randint(100, 999)
        telemetry = {random_telemetry_key: random_telemetry_val}

        with patch('skills.anomaly_alert_dispatcher.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.dispatcher.dispatch_alert(
                severity=random_severity,
                message=random_message,
                telemetry=telemetry
            )

            self.assertTrue(result)
            mock_post.assert_called_once()
            
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], self.random_endpoint)
            self.assertEqual(kwargs['headers']['Authorization'], f"Bearer {self.random_token}")
            self.assertEqual(kwargs['timeout'], self.random_timeout)
            
            payload = kwargs['json']
            self.assertEqual(payload['severity'], random_severity)
            self.assertEqual(payload['message'], random_message)
            self.assertEqual(payload['telemetry'][random_telemetry_key], random_telemetry_val)

    def test_dispatch_alert_invalid_endpoint(self):
        dispatcher_no_endpoint = AnomalyAlertDispatcher(endpoint="")
        random_severity = random.choice(['INFO', 'ERROR'])
        random_message = uuid.uuid4().hex

        with self.assertRaises(AnomalyAlertDispatcherError) as context:
            dispatcher_no_endpoint.dispatch_alert(random_severity, random_message)
        
        self.assertIn("Invalid endpoint", str(context.exception))

    def test_dispatch_alert_request_exception(self):
        random_severity = random.choice(['WARNING', 'FATAL'])
        random_message = uuid.uuid4().hex
        random_error_msg = uuid.uuid4().hex

        with patch('skills.anomaly_alert_dispatcher.requests.post') as mock_post:
            mock_post.side_effect = requests.RequestException(random_error_msg)

            with self.assertRaises(AnomalyAlertDispatcherError) as context:
                self.dispatcher.dispatch_alert(random_severity, random_message)
            
            self.assertIn("Failed to dispatch alert", str(context.exception))
            self.assertIn(random_error_msg, str(context.exception))

    def test_dispatch_alert_integration_function_with_logger(self):
        random_dispatch_id = uuid.uuid4().hex
        random_target = uuid.uuid4().hex
        random_anomaly_msg = uuid.uuid4().hex

        mock_audit_hub = MagicMock()
        mock_logger = MagicMock()
        mock_logger.get_anomalies.return_value = [random_anomaly_msg]
        mock_audit_hub.logger = mock_logger

        payload = dispatch_alert(mock_audit_hub, random_target, random_dispatch_id)

        self.assertEqual(payload["dispatch_id"], random_dispatch_id)
        self.assertEqual(payload["target_service"], random_target)
        self.assertEqual(payload["status"], "dispatched")
        self.assertIn(random_anomaly_msg, payload["anomalies"])
        mock_logger.get_anomalies.assert_called_once()

    def test_dispatch_alert_integration_function_direct_method(self):
        random_dispatch_id = uuid.uuid4().hex
        random_target = uuid.uuid4().hex
        random_anomaly_msg = uuid.uuid4().hex

        mock_audit_hub = MagicMock()
        del mock_audit_hub.logger
        mock_audit_hub.get_anomalies.return_value = [random_anomaly_msg]

        payload = dispatch_alert(mock_audit_hub, random_target, random_dispatch_id)

        self.assertEqual(payload["dispatch_id"], random_dispatch_id)
        self.assertEqual(payload["target_service"], random_target)
        self.assertEqual(payload["status"], "dispatched")
        self.assertIn(random_anomaly_msg, payload["anomalies"])
        mock_audit_hub.get_anomalies.assert_called_once()


if __name__ == '__main__':
    unittest.main()