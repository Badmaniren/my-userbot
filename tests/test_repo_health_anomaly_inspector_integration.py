import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_real_integration_flow(self):
        random_repo_id = str(uuid.uuid4())
        
        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        
        random_threshold = float(random.randint(10, 50))
        
        result = inspector.inspect(repo_id=random_repo_id, threshold=random_threshold)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('repo_id'), random_repo_id)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'inspected')
        self.assertIn('anomalies', result)
        self.assertIn('is_anomaly', result)
        self.assertIn('deviation_score', result)
        self.assertIsInstance(result['anomalies'], list)
        self.assertIsInstance(result['is_anomaly'], bool)
        self.assertIsInstance(result['deviation_score'], float)

if __name__ == '__main__':
    unittest.main()