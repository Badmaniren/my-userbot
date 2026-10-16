import unittest
import uuid
import random
import os
import tempfile
import shutil
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.anomaly_detector import AnomalyDetectorError
from skills.git_inspector import GitInspector

class TestAnomalyVisualizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Initialize a dummy git repo structure for GitInspector integration
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Arch Test'")
        os.system(f"git -C {self.repo_path} config user.email 'arch@test.com'")
        
        self.dummy_file = os.path.join(self.repo_path, "system_metrics.log")
        self.random_data_id = str(uuid.uuid4())
        
        with open(self.dummy_file, "w") as f:
            f.write(f"INIT_LOG_ID: {self.random_data_id}\n")
            
        os.system(f"git -C {self.repo_path} add system_metrics.log")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit {self.random_data_id}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_visualizer_real_git_integration_and_artifacts(self):
        anomaly_score = round(random.uniform(0.1, 0.99), 4)
        run_identifier = f"run_{uuid.uuid4().hex[:8]}"
        
        with open(self.dummy_file, "a") as f:
            f.write(f"ANOMALY_SCORE: {anomaly_score} RUN: {run_identifier}\n")
            
        os.system(f"git -C {self.repo_path} add system_metrics.log")
        os.system(f"git -C {self.repo_path} commit -m 'Update metrics {run_identifier}'")

        git_inspector = GitInspector(repo_path=self.repo_path)
        history = git_inspector.get_commit_history(max_count=5)
        self.assertTrue(len(history) >= 2)

        visualizer = AnomalyVisualizer(git_inspector=git_inspector, output_dir=self.test_dir)
        
        metric_values = [random.gauss(100, 15) for _ in range(10)]
        metric_values.append(anomaly_score * 1000)

        report_filename = f"report_{uuid.uuid4().hex}.html"
        generated_report_path = visualizer.generate_statistical_report(
            data=metric_values,
            filename=report_filename,
            metadata={"run_id": run_identifier, "score": anomaly_score}
        )

        self.assertTrue(os.path.exists(generated_report_path), "Интеграционный тест не обнаружил созданный файл отчета визуализации.")
        
        with open(generated_report_path, "r", encoding="utf-8") as rep:
            content = rep.read()
            self.assertIn(run_identifier, content, "Отчет не содержит уникальный идентификатор выполнения.")
            self.assertIn(str(anomaly_score), content, "Отчет не содержит переданный коэффициент аномалии.")

if __name__ == "__main__":
    unittest.main()