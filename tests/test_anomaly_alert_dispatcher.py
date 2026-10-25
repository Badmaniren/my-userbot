import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_alert_dispatcher import AnomalyAlertDispatcher, AnomalyAlertDispatcherError, dispatch_alert

class TestAnomalyAlertDispatcherInquisition(unittest.TestCase):
    
    def setUp(self):
        self.endpoint = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.api_token = uuid.uuid4().hex
        self.timeout = random.randint(1, 15)
        self.dispatcher = AnomalyAlertDispatcher(endpoint=self.endpoint, api_token=self.api_token, timeout=self.timeout)

    def test_init_properties(self):
        rand_ep = f"http://{uuid.uuid4().hex}.net"
        rand_token = uuid.uuid4().hex
        rand_timeout = random.randint(5, 20)
        disp = AnomalyAlertDispatcher(endpoint=rand_ep, api_token=rand_token, timeout=rand_timeout)
        self.assertEqual(disp.endpoint, rand_ep)
        self.assertEqual(disp.api_token, rand_token)
        self.assertEqual(disp.timeout, rand_timeout)

    def test_dispatch_alert_invalid_endpoint(self):
        bad_disp = AnomalyAlertDispatcher(endpoint="", api_token=self.api_token)
        severity = random.choice(["LOW", "MEDIUM", "CRITICAL"])
        message = "".join(random.choices(string.ascii_letters, k=10))
        with self.assertRaises(AnomalyAlertDispatcherError):
            bad_disp.dispatch_alert(severity, message)

    def test_dispatch_alert_success(self):
        severity = random.choice(["WARNING", "FATAL", "INFO"])
        message = uuid.uuid4().hex
        telemetry = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.dispatcher.dispatch_alert(severity, message, telemetry=telemetry)
            self.assertTrue(result)

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], self.endpoint)
            self.assertEqual(kwargs["headers"]["Authorization"], f"Bearer {self.api_token}")
            self.assertEqual(kwargs["timeout"], self.timeout)
            self.assertEqual(kwargs["json"]["severity"], severity)
            self.assertEqual(kwargs["json"]["message"], message)
            self.assertEqual(kwargs["json"]["telemetry"], telemetry)

    def test_dispatch_alert_without_token(self):
        disp_no_token = AnomalyAlertDispatcher(endpoint=self.endpoint, api_token=None)
        severity = uuid.uuid4().hex
        message = uuid.uuid4().hex

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response

            disp_no_token.dispatch_alert(severity, message)
            _, kwargs = mock_post.call_args
            self.assertNotIn("Authorization", kwargs["headers"])

    def test_dispatch_alert_request_exception(self):
        severity = uuid.uuid4().hex
        message = uuid.uuid4().hex

        with patch("requests.post", side_effect=Exception(uuid.uuid4().hex)) as mock_post:
            with self.assertRaises(AnomalyAlertDispatcherError):
                self.dispatcher.dispatch_alert(severity, message)

    def test_dispatch_alert_helper_function_with_logger_method(self):
        dispatch_id = uuid.uuid4().hex
        target_service = uuid.uuid4().hex
        anomaly_item = {"source": uuid.uuid4().hex, "severity": "HIGH"}
        
        audit_hub = MagicMock()
        audit_hub.logger = MagicMock()
        audit_hub.logger.get_anomalies.return_value = [anomaly_item]
        
        # Удаляем метод get_anomalies из audit_hub чтобы сработал путь через audit_hub.logger
        del audit_hub.get_anomalies

        payload = dispatch_alert(audit_hub, target_service, dispatch_id)
        
        self.assertEqual(payload["dispatch_id"], dispatch_id)
        self.assertEqual(payload["target_service"], target_service)
        self.assertEqual(payload["status"], "dispatched")
        self.assertEqual(payload["anomalies"], [anomaly_item])

    def test_dispatch_alert_helper_function_with_direct_method(self):
        dispatch_id = uuid.uuid4().hex
        target_service = uuid.uuid4().hex
        anomaly_item = {"source": uuid.uuid4().hex, "severity": "CRITICAL"}
        
        audit_hub = MagicMock()
        # Имитируем отсутствие логгера или отсутствие у него метода get_anomalies
        audit_hub.logger = None
        audit_hub.get_anomalies.return_value = [anomaly_item]

        payload = dispatch_alert(audit_hub, target_service, dispatch_id)
        
        self.assertEqual(payload["dispatch_id"], dispatch_id)
        self.assertEqual(payload["target_service"], target_service)
        self.assertEqual(payload["status"], "dispatched")
        self.assertEqual(payload["anomalies"], [anomaly_item])

    def test_dispatch_alert_helper_function_no_anomalies(self):
        dispatch_id = uuid.uuid4().hex
        target_service = uuid.uuid4().hex
        
        audit_hub = MagicMock()
        audit_hub.logger = None
        # Удаляем метод get_anomalies
        del audit_hub.get_anomalies

        payload = dispatch_alert(audit_hub, target_service, dispatch_id)
        
        self.assertEqual(payload["dispatch_id"], dispatch_id)
        self.assertEqual(payload["target_service"], target_service)
        self.assertEqual(payload["status"], "dispatched")
        self.assertEqual(payload["anomalies"], [])