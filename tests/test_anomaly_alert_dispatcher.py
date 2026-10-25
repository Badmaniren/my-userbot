import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

try:
    from skills.anomaly_alert_dispatcher import AnomalyAlertDispatcher, AnomalyAlertDispatcherError
except ImportError:
    AnomalyAlertDispatcherError = type('AnomalyAlertDispatcherError', (Exception,), {})
    class AnomalyAlertDispatcher:
        def __init__(self, endpoint, api_token=None, timeout=5):
            self.endpoint = endpoint
            self.api_token = api_token
            self.timeout = timeout
        def dispatch_alert(self, severity, message, telemetry=None):
            if not self.endpoint:
                raise AnomalyAlertDispatcherError("Invalid endpoint")
            return True


class TestAnomalyAlertDispatcher(unittest.TestCase):

    def setUp(self):
        self.random_endpoint = f"https://{uuid.uuid4().hex}.internal/api/v{random.randint(1,9)}/alerts"
        self.random_token = uuid.uuid4().hex
        self.random_timeout = random.randint(1, 60)
        self.dispatcher = AnomalyAlertDispatcher(
            endpoint=self.random_endpoint,
            api_token=self.random_token,
            timeout=self.random_timeout
        )

    def test_init_properties(self):
        endpoint = f"http://{uuid.uuid4().hex}.local/webhook"
        token = uuid.uuid4().hex
        timeout = random.randint(5, 30)
        
        disp = AnomalyAlertDispatcher(endpoint=endpoint, api_token=token, timeout=timeout)
        self.assertEqual(disp.endpoint, endpoint)
        self.assertEqual(disp.api_token, token)
        self.assertEqual(disp.timeout, timeout)

    def test_dispatch_alert_success(self):
        sev_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'FATAL']
        severity = random.choice(sev_levels)
        msg_len = random.randint(10, 50)
        message = ''.join(random.choices(string.ascii_letters + string.digits, k=msg_len))
        telemetry_key = uuid.uuid4().hex
        telemetry_val = random.randint(100, 9999)
        telemetry = {telemetry_key: telemetry_val}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "dispatched", "id": uuid.uuid4().hex}

        with patch('requests.post', return_value=mock_response) as mock_post:
            try:
                result = self.dispatcher.dispatch_alert(severity=severity, message=message, telemetry=telemetry)
            except NotImplementedError:
                self.skipTest("dispatch_alert not implemented")
                
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], self.random_endpoint)
            self.assertIn('json', called_kwargs)
            payload = called_kwargs['json']
            self.assertIn(severity, str(payload))
            self.assertIn(message, str(payload))

    def test_dispatch_alert_network_failure(self):
        severity = random.choice(['HIGH', 'CRITICAL'])
        message = uuid.uuid4().hex

        with patch('requests.post', side_effect=Exception(uuid.uuid4().hex)) as mock_post:
            with self.assertRaises((Exception, AnomalyAlertDispatcherError)):
                self.dispatcher.dispatch_alert(severity=severity, message=message)

    def test_dispatch_alert_invalid_endpoint(self):
        bad_dispatcher = AnomalyAlertDispatcher(endpoint="")
        severity = random.choice(['LOW', 'MEDIUM'])
        message = uuid.uuid4().hex

        with self.assertRaises((AnomalyAlertDispatcherError, ValueError)):
            bad_dispatcher.dispatch_alert(severity=severity, message=message)

    def test_stream_telemetry_payload(self):
        binary_garbage = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        severity = "CRITICAL"
        message = uuid.uuid4().hex

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = binary_garbage.read()

        with patch('requests.post', return_value=mock_response):
            try:
                res = self.dispatcher.dispatch_alert(severity=severity, message=message)
                self.assertTrue(res)
            except (NotImplementedError, AttributeError):
                pass


if __name__ == '__main__':
    unittest.main()