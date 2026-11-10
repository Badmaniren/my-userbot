import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_health_incident_tracker import track_incident
from skills.repo_health_anomaly_inspector import inspect_anomaly
from skills.repo_logger import log_repo_event


class TestRepoHealthIncidentTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.anomaly_id = f"anomaly-{uuid.uuid4()}"
        self.severity_levels = ["LOW