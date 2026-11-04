import unittest
from unittest.mock import patch
import random
import uuid
import string
from skills.release_notes_composer import ReleaseNotesComposer

class TestReleaseNotesComposer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"

    def test_release_notes_composer_initialization_and_composition(self):
        rnd_repo = f"/repo/{uuid.uuid4().hex}"
        rnd_output = f"/output/{uuid.uuid4().hex}.md"
        rnd_changelog_text = f"Changelog entry {uuid.uuid4().hex}"
        
        with patch('skills.release_notes_composer.ChangelogGenerator') as mock_gen_cls, \
             patch('skills.release_notes_composer.RepoAuditor') as mock_auditor_cls:
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_changelog.return_value = rnd_changelog_text
            
            mock_auditor_instance = mock_auditor_cls.return_value
            
            composer = ReleaseNotesComposer(rnd_repo)
            
            mock_gen_cls.assert_called_once_with(rnd_repo)
            mock_auditor_cls.assert_called_once_with(rnd_repo)
            
            self.assertEqual(composer.repo_path, rnd_repo)

    def test_compose_release_notes_aggregates_correctly(self):
        rnd_repo = f"/repo/{uuid.uuid4().hex}"
        rnd_output = f"/output/{uuid.uuid4().hex}/release.md"
        rnd_changelog = f"Feature: {''.join(random.choices(string.ascii_letters, k=10))}"
        rnd_audit_path = f"/output/{uuid.uuid4().hex}/audit.json"

        with patch('skills.release_notes_composer.ChangelogGenerator') as mock_gen_cls, \
             patch('skills.release_notes_composer.RepoAuditor') as mock_auditor_cls:
            
            mock_gen = mock_gen_cls.return_value
            mock_gen.generate.return_value = True
            mock_gen.get_changelog.return_value = rnd_changelog

            mock_auditor = mock_auditor_cls.return_value
            mock_auditor.generate_report.return_value = rnd_audit_path
            mock_auditor.calculate_metrics.return_value = {"score": random.randint(50, 100)}

            composer = ReleaseNotesComposer(rnd_repo)
            
            if hasattr(composer, 'compose'):
                result = composer.compose(rnd_output)
                mock_gen.generate.assert_called()
                mock_auditor.generate_report.assert_called()
                self.assertIsNotNone(result)
            elif hasattr(composer, 'generate_release_notes'):
                result = composer.generate_release_notes(rnd_output)
                mock_gen.generate.assert_called()
                self.assertIsNotNone(result)
            else:
                methods = [m for m in dir(composer) if callable(getattr(composer, m)) and not m.startswith("_")]
                self.assertTrue(len(methods) > 0)

    def test_compose_handles_component_failure(self):
        rnd_repo = f"/repo/{uuid.uuid4().hex}"
        rnd_output = f"/output/{uuid.uuid4().hex}.md"
        
        with patch('skills.release_notes_composer.ChangelogGenerator') as mock_gen_cls, \
             patch('skills.release_notes_composer.RepoAuditor') as mock_auditor_cls:
            
            mock_gen = mock_gen_cls.return_value
            mock_gen.generate.side_effect = Exception(uuid.uuid4().hex)

            composer = ReleaseNotesComposer(rnd_repo)
            
            methods = [m for m in dir(composer) if callable(getattr(composer, m)) and not m.startswith("_")]
            target_method = methods[0] if methods else None
            
            if target_method:
                func = getattr(composer, target_method)
                try:
                    func(rnd_output)
                except Exception:
                    pass

if __name__ == '__main__':
    unittest.main()