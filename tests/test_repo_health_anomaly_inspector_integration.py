import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_integration_real_pulse_engine(self):
        inspector = RepoHealthAnomalyInspector()
        
        random_repo_id = str(uuid.uuid4())
        random_threshold = float(random.randint(10, 50))
        
        result = inspector.inspect(
            repo_id=random_repo_id, 
            threshold=random_threshold
        )