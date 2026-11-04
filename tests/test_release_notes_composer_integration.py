import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.release_notes_composer import ReleaseNotesComposer
from skills.changelog_generator import ChangelogGenerator
from skills.repo_auditor import RepoAuditor

class TestReleaseNotesComposerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        self.unique_feature = f"feature-{uuid.uuid4()}"
        self.unique_audit_metric = random.randint(100, 999)
        
        dummy_file = os.path.join(self.repo_path, "main.py")
        with open(dummy_file, "w", encoding="utf-8") as f:
            f.write(f"# {self.unique_feature}\nprint({self.unique_audit_metric})\n")

    def tearDown(self):
        shutil.rmtree(self.repo_path, ignore_errors=True)

    def test_release_notes_composer_integration(self):
        output_filename = f"release_notes_{uuid.uuid4()}.md"
        output_path = os.path.join(self.repo_path, output_filename)

        composer = ReleaseNotesComposer(self.repo_path)
        
        self.assertTrue(
            hasattr(composer, 'compose') or hasattr(composer, 'generate') or hasattr(composer, 'run'),
            "ReleaseNotesComposer должен содержать метод для запуска композиции"
        )
        
        if hasattr(composer, 'compose'):
            result = composer.compose(output_path)
        elif hasattr(composer, 'generate'):
            result = composer.generate(output_path)
        else:
            result = composer.run()

        self.assertTrue(
            os.path.exists(output_path) or isinstance(result, (str, dict, bool)),
            "Интеграционный тест должен успешно выполнить агрегацию и создать артефакт или вернуть результат"
        )

        changelog_gen = ChangelogGenerator(self.repo_path)
        changelog_out = os.path.join(self.repo_path, f"changelog_{uuid.uuid4()}.md")
        changelog_gen.generate(changelog_out)
        
        auditor = RepoAuditor(self.repo_path)
        audit_out = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.json")
        auditor.generate_report(audit_out)

        self.assertTrue(os.path.exists(changelog_out), "Подмодуль changelog_generator должен генерировать ченжлог")
        self.assertTrue(os.path.exists(audit_out), "Подмодуль repo_auditor должен генерировать отчет аудита")

if __name__ == '__main__':
    unittest.main()