import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.incident_predictive_risk_model import start_new

class TestIncidentPredictiveRiskModelStartNew(unittest.TestCase):

    def test_start_new_endpoint_request(self):
        rand_endpoint = f"http://{uuid.uuid4().hex}.local/api"
        rand_payload = uuid.uuid4().hex
        rand_threshold = random.uniform(1.0, 100.0)

        with patch('skills.incident_predictive_risk_model.requests.post') as mock_post:
            start_new(endpoint=rand_endpoint, payload=rand_payload, threshold=rand_threshold)
            mock_post.assert_called_once_with(rand_endpoint, json={"payload": rand_payload, "threshold": rand_threshold})

    def test_start_new_audit_bridge(self):
        rand_token = uuid.uuid4().hex
        mock_bridge = MagicMock()

        with patch('skills.incident_predictive_risk_model.telemetry_anomaly_audit_bridge', mock_bridge):
            start_new(audit_token=rand_token)
            mock_bridge.log_event.assert_called_once_with(token=rand_token)

    def test_start_new_system_risk_evaluator(self):
        rand_target = uuid.uuid4().hex
        rand_limit = random.uniform(0.0, 1.0)
        mock_evaluator = MagicMock()

        with patch('skills.incident_predictive_risk_model.system_risk_evaluator', mock_evaluator):
            start_new(target=rand_target, probability_limit=rand_limit)
            mock_evaluator.evaluate.assert_called_once_with(target=rand_target, limit=rand_limit)

    def test_start_new_comprehensive_call(self):
        rand_endpoint = f"http://{uuid.uuid4().hex}.test/endpoint"
        rand_payload = "".join(random.choices(string.ascii_letters, k=10))
        rand_threshold = random.randint(1, 50)
        rand_token = uuid.uuid4().hex
        rand_target = uuid.uuid4().hex
        rand_limit = random.random()

        mock_bridge = MagicMock()
        mock_evaluator = MagicMock()

        with patch('skills.incident_predictive_risk_model.requests.post') as mock_post, \
             patch('skills.incident_predictive_risk_model.telemetry_anomaly_audit_bridge', mock_bridge), \
             patch('skills.incident_predictive_risk_model.system_risk_evaluator', mock_evaluator):

            result = start_new(
                endpoint=rand_endpoint,
                payload=rand_payload,
                threshold=rand_threshold,
                audit_token=rand_token,
                target=rand_target,
                probability_limit=rand_limit
            )

            self.assertIsNone(result)
            mock_post.assert_called_once_with(rand_endpoint, json={"payload": rand_payload, "threshold": rand_threshold})
            mock_bridge.log_event.assert_called_once_with(token=rand_token)
            mock_evaluator.evaluate.assert_called_once_with(target=rand_target, limit=rand_limit)

    def test_start_new_no_actions(self):
        with patch('skills.incident_predictive_risk_model.requests.post') as mock_post:
            result = start_new()
            self.assertIsNone(result)
            mock_post.assert_not_called()

if __name__ == '__main__':
    unittest.main()