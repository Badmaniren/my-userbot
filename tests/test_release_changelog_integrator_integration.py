import unittest
import os
import uuid
import random
from skills.release_changelog_integrator import ReleaseChangelogIntegrator, release_changelog_integrator

class TestReleaseChangelogIntegratorIntegration(unittest.TestCase):
    def setUp(self):
        self.integrator = ReleaseChangelogIntegrator()
        self.random_uuid = str(uuid.uuid4())
        self.random_version = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.test_repo_path = f"./test_repo_{self.random_uuid}"
        os