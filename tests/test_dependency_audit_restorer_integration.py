import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.dependency_audit_restorer import audit_and_restore_dependencies
from skills.repo_recovery import RepoRecovery


class TestDependencyAuditRestorerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix=f"audit_restorer_test_{uuid.uuid4().hex}_")
        self.repo_path = self.test_dir
        
        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)
        
        self.branch_name = f"feature-audit-{uuid.uuid4().hex[:8]}"
        self.stream_source = f"stream-{random.randint(1000, 9999)}"
        self.output_report = f"report_{uuid.uuid4().hex}.json"
        self.cve_id