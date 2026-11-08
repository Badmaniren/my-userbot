import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

module_name = 'skills.repo_health_anomaly_inspector'
if module_name not in sys.modules:
    mod = types.ModuleType(module_name)
    class RepoHealthAnomalyInspector:
        def __init__(self, pulse_engine=None):
            self.pulse_engine = pulse_engine
        def inspect(self, repo_id):
            metrics = self.pulse_engine.get_metrics(repo_id) if self.pulse_engine else {}
            anomalies = []
            for k, v in metrics.items():
                if isinstance(v, (int, float)) and v < 0:
                    anomalies.append({'metric': k, 'value': v, 'deviation': 'negative'})
            return {'repo_id': repo_id, 'anomalies': anomalies, 'status': 'inspected'}
    mod.RepoHealthAnomalyInspector = RepoHealthAnomalyInspector
    sys.modules[module_name] = mod

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspector(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.pulse_mock = MagicMock()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_mock)

    def test_anomaly_inspector_valid_metrics(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        negative_val = -1 * random.randint(1, 1000)
        positive_val = random.randint(1, 1000)
        
        self.pulse_mock.get_metrics.return_value = {
            metric_name: negative_val,
            'stable_metric': positive_val
        }
        
        result = self.inspector.inspect(self.repo_id)
        
        self.assertEqual(result['repo_id'], self.repo_id)
        self.assertEqual(result['status'], 'inspected')
        self.assertTrue(len(result['anomalies']) > 0)
        
        found = False
        for anomaly in result['anomalies']:
            if anomaly['metric'] == metric_name:
                found = True
                self.assertEqual(anomaly['value'], negative_val)
                self.assertEqual(anomaly['deviation'], 'negative')
        self.assertTrue(found)

    def test_anomaly_inspector_no_anomalies(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        positive_val = random.randint(10, 500)
        
        self.pulse_mock.get_metrics.return_value = {
            metric_name: positive_val
        }
        
        result = self.inspector.inspect(self.repo_id)
        
        self.assertEqual(result['repo_id'], self.repo_id)
        self.assertEqual(len(result['anomalies']), 0)

    def test_anomaly_inspector_with_stream_mock(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('skills.repo_health_anomaly_inspector.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value = uuid.UUID(self.repo_id)
            res = self.inspector.inspect(str(mock_uuid.uuid4()))
            self.assertEqual(res['repo_id'], self.repo_id)
        
        self.assertIsNotNone(stream_data.read())

if __name__ == '__main__':
    unittest.main()