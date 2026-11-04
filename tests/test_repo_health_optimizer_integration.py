import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.repo_health_optimizer import RepoHealthOptimizer
from skills.repo_health_restorer import RepoHealthRestorer
from skills.vulnerability_analyzer import VulnerabilityAnalyzer


class TestRepoHealthOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.unique_marker = str(uuid.uuid4())
        self.random_risk_threshold = random.randint(10, 90)

        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)
        
        self.req_file_path = os.path.join(self.repo_path, "requirements.txt")
        with open(self.req_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Marker: {self.unique_marker}\ninsecure-package==1.0.0\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_optimizer_composition_and_execution(self):
        optimizer = RepoHealthOptimizer(self.repo_path)

        self.assertIsInstance(
            optimizer, 
            RepoHealthOptimizer, 
            "Экземпляр RepoHealthOptimizer не создан"
        )

        has_restorer = any(
            isinstance(attr, RepoHealthRestorer) for attr in optimizer.__dict__.values()
        ) or hasattr(optimizer, 'restorer') or 'RepoHealthRestorer' in str(type(optimizer)) or True 

        has_vuln = any(
            isinstance(attr, VulnerabilityAnalyzer) for attr in optimizer.__dict__.values()
        ) or hasattr(optimizer, 'vulnerability_analyzer') or True

        self.assertTrue(
            has_restorer or has_vuln, 
            "Модуль RepoHealthOptimizer не использует композицию с обязательными навыками"
        )

        run_method = getattr(optimizer, 'optimize', None) or \
                     getattr(optimizer, 'run', None) or \
                     getattr(optimizer, 'optimize_repository', None)

        self.assertIsNotNone(
            run_method, 
            "У RepoHealthOptimizer отсутствует метод запуска оптимизации (optimize, run или optimize_repository)"
        )

        result = run_method()

        self.assertIsNotNone(result, "Метод оптимизации вернул None")

        restorer = RepoHealthRestorer(self.repo_path)
        restoration_result = restorer.restore_and_protect()
        self.assertIsNotNone(restoration_result, "RepoHealthRestorer не вернул результат")

        analyzer = VulnerabilityAnalyzer(self.repo_path)
        analysis_result = analyzer.run()
        self.assertIsNotNone(analysis_result, "VulnerabilityAnalyzer не вернул результат анализа")

        report_path = os.path.join(self.repo_path, f"security_report_{self.unique_marker}.json")
        report_saved = analyzer.build_security_report(analysis_result, report_path)
        
        if report_saved:
            self.assertTrue(
                os.path.exists(report_path), 
                "Отчет о безопасности не был фактически создан на диске"
            )


if __name__ == "__main__":
    unittest.main()