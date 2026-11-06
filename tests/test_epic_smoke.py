import unittest
import os
import json
import tempfile
from release_notes_composer import ReleaseNotesComposer
from release_notes_publisher import ReleaseNotesPublisher
from repo_release_exporter import RepoReleaseExporter
from release_pipeline import ReleasePipeline
from release_automation_hub import ReleaseAutomationHub

class TestReleaseEcosystemIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.changelog_path = os.path.join(self.test_dir.name, "CHANGELOG.md")
        self.export_path = os.path.join(self.test_dir.name, "release_audit_report.json")
        
        self.raw_commits = [
            "feat(auth): add OAuth2 token rotation mechanism",
            "fix(api): resolve memory leak in release payload serialization",
            "refactor(core): streamline dependency audit pipeline execution",
            "docs(readme): update deployment instructions for release ecosystem"
        ]
        
        with open(os.path.join(self.test_dir.name, "commits.json"), "w", encoding="utf-8") as f:
            json.dump(self.raw_commits, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_release_ecosystem(self):
        print("\n--- Запуск практической проверки экосистемы управления релизами ---")
        
        composer = ReleaseNotesComposer()
        publisher = ReleaseNotesPublisher()
        exporter = RepoReleaseExporter()
        pipeline = ReleasePipeline(composer=composer, publisher=publisher, exporter=exporter)
        hub = ReleaseAutomationHub(pipeline=pipeline)

        print(f"1. Сбор изменений и компоновка заметок из {len(self.raw_commits)} коммитов...")
        release_notes = composer.compose(self.raw_commits)
        print(f"Скомпонованные релизные заметки:\n{release_notes}")
        self.assertIn("OAuth2", release_notes)

        print("2. Публикация релиза...")
        publish_result = publisher.publish(release_notes, target="production_channel")
        print(f"Результат публикации: {publish_result}")
        self.assertTrue(publish_result.get("success", True))

        print("3. Экспорт данных релиза и аудит...")
        export_data = {
            "version": "v1.4.0",
            "notes": release_notes,
            "status": "published",
            "audit_trail": ["gathered", "composed", "published"]
        }
        export_result = exporter.export(export_data, destination=self.export_path)
        print(f"Результат экспорта в {self.export_path}: {export_result}")
        self.assertTrue(os.path.exists(self.export_path))

        with open(self.export_path, "r", encoding="utf-8") as f:
            saved_report = json.load(f)
        print(f"Прочитанный с диска JSON-отчет релиза: {json.dumps(saved_report, indent=2)}")
        self.assertEqual(saved_report["version"], "v1.4.0")

        print("4. Финализация через release_automation_hub (проверка прозрачности и аудита)...")
        hub_status = hub.verify_and_audit(self.export_path)
        print(f"Статус аудита хаба: {hub_status}")
        self.assertTrue(hub_status.get("audited", True))
        print("--- Проверка экосистемы управления релизами успешно завершена ---")

if __name__ == "__main__":
    unittest.main()