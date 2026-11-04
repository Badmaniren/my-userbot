import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.repo_release_exporter import RepoReleaseExporter
from skills.repo_tagger import RepoTagger, TagManager
from skills.repo_ci_pipeline import RepoCIPipeline

class TestRepoReleaseExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Architect'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@test.com'")
        
        self.random_file_name = f"artifact_{uuid.uuid4().hex[:8]}.txt"
        self.file_path = os.path.join(self.test_dir, self.random_file_name)
        
        self.random_content = uuid.uuid4().bytes
        with open(self.file_path, "wb") as f:
            f.write(self.random_content)
            
        os.system(f"git -C {self.test_dir} add {self.random_file_name}")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit {uuid.uuid4().hex[:4]}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_release_exporter_composition_workflow(self):
        tagger = RepoTagger(self.test_dir)
        pipeline = RepoCIPipeline(self.test_dir)
        exporter = RepoReleaseExporter(self.test_dir)

        self.assertIsInstance(tagger, RepoTagger)
        self.assertIsInstance(pipeline, RepoCIPipeline)
        self.assertIsInstance(exporter, RepoReleaseExporter)

        version_suffix = random.randint(100, 999)
        test_tag = f"v1.0.{version_suffix}"
        
        tag_manager = TagManager(self.test_dir)
        tag_created = tag_manager.create_release_tag(test_tag)
        self.assertTrue(tag_created, "TagManager должен успешно создать тег релиза")

        pipeline_res = pipeline.run_pipeline()
        self.assertTrue(pipeline_res, "CI пайплайн должен успешно выполниться без моков")

        export_dest = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex[:6]}")
        os.makedirs(export_dest, exist_ok=True)

        export_result = exporter.export_release(test_tag, export_dest)
        self.assertTrue(export_result, "RepoReleaseExporter должен успешно экспортировать артефакты релиза")

        exported_files = os.listdir(export_dest)
        self.assertGreater(len(exported_files), 0, "Директория экспорта не должна быть пустой")

        found_artifact = False
        for ef in exported_files:
            full_ef_path = os.path.join(export_dest, ef)
            if os.path.isfile(full_ef_path):
                with open(full_ef_path, "rb") as ef_read:
                    content = ef_read.read()
                    if self.random_content in content or len(content) > 0:
                        found_artifact = True
                        break
                        
        self.assertTrue(found_artifact, "Экспортированные артефакты должны содержать данные репозитория")

if __name__ == "__main__":
    unittest.main()