import os
import io
import unittest
import uuid
import random
import sys
import types
from unittest.mock import patch, MagicMock

mock_modules = [
    'vulnerability_analyzer',
    'dependency_updater_pipeline',
    'repo_reporter'
]
for mod_name in mock_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

from skills.release_changelog_integrator import (
    ReleaseChangelogIntegrator,
    release_changelog_integrator
)


class TestReleaseChangelogIntegrator(unittest.TestCase):

    def test_integrate_success(self):
        rand_version = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        rand_content = uuid.uuid4().hex
        rand_hub_id = uuid.uuid4().hex

        integrator = ReleaseChangelogIntegrator()

        with patch('skills.release_changelog_integrator.release_notes_composer') as mock_composer, \
             patch('skills.release_changelog_integrator.hub_module') as mock_hub:

            mock_composer.compose.return_value = rand_content
            mock_hub.push_release.return_value = rand_hub_id

            result_id = integrator.integrate(rand_version)

            mock_composer.compose.assert_called_once_with(rand_version)
            mock_hub.push_release.assert_called_once_with(rand_content)
            self.assertEqual(result_id, rand_hub_id)

    def test_parse_changelog_file(self):
        rand_filename = f"{uuid.uuid4().hex}.md"
        rand_text = f"Changelog entry {uuid.uuid4().hex}"
        file_bytes = rand_text.encode('utf-8')

        integrator = ReleaseChangelogIntegrator()

        with patch('builtins.open', unittest.mock.mock_open(read_data=file_bytes)) as mock_file:
            parsed_data = integrator.parse_changelog_file(rand_filename)
            mock_file.assert_called_once_with(rand_filename, 'rb')
            self.assertEqual(parsed_data, rand_text)

    def test_sync_with_hub(self):
        rand_url = f"https://{uuid.uuid4().hex}.com/hub/sync"
        integrator = ReleaseChangelogIntegrator()

        with patch('skills.release_changelog_integrator.dependency_audit_sync') as mock_sync:
            integrator.sync_with_hub(rand_url)
            mock_sync.sync.assert_called_once_with(rand_url)

    def test_run_audit(self):
        rand_audit_id = uuid.uuid4().hex
        rand_threshold = round(random.uniform(0.1, 0.9), 2)
        expected_result = random.choice([True, False])

        integrator = ReleaseChangelogIntegrator()

        with patch('skills.release_changelog_integrator.dependency_audit_pipeline') as mock_pipeline:
            mock_pipeline.run.return_value = expected_result

            res = integrator.run_audit(rand_audit_id, rand_threshold)

            mock_pipeline.run.assert_called_once_with(audit_id=rand_audit_id, threshold=rand_threshold)
            self.assertEqual(res, expected_result)

    def test_get_repo_health(self):
        rand_repo_name = f"repo-{uuid.uuid4().hex[:8]}"
        expected_score = random.randint(1, 100)

        integrator = ReleaseChangelogIntegrator()

        with patch('skills.release_changelog_integrator.repo_health_automator') as mock_health:
            mock_health.get_score.return_value = expected_score

            score = integrator.get_repo_health(rand_repo_name)

            mock_health.get_score.assert_called_once_with(rand_repo_name)
            self.assertEqual(score, expected_score)

    def test_functional_release_changelog_integrator(self):
        rand_repo_path = f"/tmp/{uuid.uuid4().hex}"
        rand_version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.0"
        rand_integration_id = uuid.uuid4().hex
        rand_hub_status = uuid.uuid4().hex

        payload = {
            "repo_path": rand_repo_path,
            "target_version": rand_version,
            "integration_id": rand_integration_id,
            "hub_status": rand_hub_status
        }

        mock_file_instance = MagicMock()
        mock_file_instance.return_value.__enter__.return_value = mock_file_instance.return_value
        expected_path = os.path.join(rand_repo_path, "CHANGELOG.md")

        with patch('builtins.open', mock_file_instance) as mock_open:
            response = release_changelog_integrator(payload)

            mock_open.assert_called_once_with(expected_path, "w", encoding="utf-8")

            handle = mock_open()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn(rand_version, written_content)
            self.assertIn(rand_integration_id, written_content)
            self.assertIn(rand_hub_status, written_content)

            self.assertEqual(response["status"], "synchronized")
            self.assertEqual(response["integration_id"], rand_integration_id)
            self.assertEqual(response["version"], rand_version)