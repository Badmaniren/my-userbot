import io
import os
import random
import unittest
from unittest.mock import MagicMock, patch
import uuid
import string

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_init_signatures(self):
        self.assertEqual(self.dispatcher.repo_path, self.repo_path)
        self.assertIsNotNone(self.dispatcher.repo_health_dashboard)