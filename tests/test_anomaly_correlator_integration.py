import unittest
import os
import shutil
import tempfile
import uuid
import random
import subprocess
from skills.git_inspector import GitInspector
from skills.anomaly_detector import AnomalyDetector
from skills.anomaly_correlator import AnomalyCorrelator

class TestAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_repo_path = tempfile.mkdtemp()
        self._run_git(['init'])
        self._run_git(['config', 'user.email', 'architect@example.com'])
        self._run_git(['config', 'user.name', 'Architect Admin'])

        self.metric_id = f"latency_{uuid.uuid4().hex[:6]}"
        self.git_inspector = GitInspector(self.test_repo_path)
        # threshold 0.1 to ensure sensitivity for random spikes
        self.anomaly_detector = AnomalyDetector(self.test_repo_path, 0.1, self.git_inspector, None)
        self.correlator = AnomalyCorrelator(self.git_inspector, self.anomaly_detector)

    def tearDown(self):
        if os.path.exists(self.test_repo_path):
            shutil.rmtree(self.test_repo_path)

    def _run_git(self, args):
        subprocess.run(['git'] + args, cwd=self.test_repo_path, capture_output=True, check=True)

    def _create_commit(self, message):
        filename = f"service_{uuid.uuid4().hex[:8]}.py"
        filepath = os.path.join(self.test_repo_path, filename)
        with open(filepath, 'w') as f:
            f.write(f"# Random code {random.random()}")
        self._run_git(['add', '.'])
        self._run_git(['commit', '-m', message])
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.test_repo_path, capture_output=True, text=True)
        return result.stdout.strip()

    def test_full_integration_flow_identifies_culprit(self):
        # 1. Establish baseline metrics
        for _ in range(5):
            self.anomaly_detector.record_metric(self.metric_id, random.uniform(10.0, 12.0))

        # 2. Create a 'safe' commit
        self._create_commit(f"Safe update {uuid.uuid4()}")

        # 3. Create the 'culprit' commit that triggers degradation
        culprit_msg = f"CRITICAL_CHANGE_{uuid.uuid4().hex}"
        culprit_hash = self._create_commit(culprit_msg)

        # 4. Record anomalous metrics (significant spike)
        spike_value = random.uniform(500.0, 600.0)
        self.anomaly_detector.record_metric(self.metric_id, spike_value)

        # 5. Execute detection through the detector
        anomalies = self.anomaly_detector.detect_anomalies()
        self.assertIn(self.metric_id, anomalies, "Anomaly detector failed to identify the spike")

        # 6. Execute correlation (The module under test)
        # This calls git_inspector.get_history() and matches with anomaly timestamps
        correlation_report = self.correlator.correlate(self.metric_id)

        # 7. Assertions
        self.assertIsNotNone(correlation_report)
        self.assertEqual(correlation_report['culprit_commit'], culprit_hash)
        self.assertIn(culprit_msg, correlation_report['commit_message'])

        # Verify the report contains real data from the git history
        history = self.git_inspector.get_history()
        self.assertTrue(any(culprit_hash in str(h) for h in history))

    def test_no_correlation_when_no_anomalies(self):
        # Record only stable metrics
        stable_metric = f"cpu_{uuid.uuid4().hex[:6]}"
        for _ in range(10):
            self.anomaly_detector.record_metric(stable_metric, 5.0)

        self._create_commit("Routine maintenance")

        report = self.correlator.correlate(stable_metric)
        self.assertIsNone(report, "Correlator should return None if no anomalies are found for the metric")

if __name__ == '__main__':
    unittest.main()