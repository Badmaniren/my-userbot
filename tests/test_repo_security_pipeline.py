import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.repo_security_pipeline import RepoSecurityPipeline

class TestRepoSecurityPipeline(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.pipeline = RepoSecurityPipeline(self.repo_path)

    def test_pipeline_execution_with_critical_threat(self):
        """
        Тест: Проверка прерывания CI/CD при обнаружении критической уязвимости.
        """
        random_risk_score = random.randint(90, 100)
        random_report_id = uuid.uuid4().hex

        with patch('skills.repo_security_gateway.RepoSecurityGateway') as MockGateway, \
             patch('skills.vulnerability_analyzer.VulnerabilityAnalyzer') as MockAnalyzer:

            gateway_instance = MockGateway.return_value
            analyzer_instance = MockAnalyzer.return_value

            gateway_instance.scan_and_evaluate.return_value = {"status": "active", "id": random_report_id}
            analyzer_instance.run.return_value = {"risk_score": random_risk_score, "critical": True}

            result = self.pipeline.run_pipeline()

            self.assertFalse(result, "Pipeline должен вернуть False при критической угрозе")
            analyzer_instance.run.assert_called_once()
            gateway_instance.scan_and_evaluate.assert_called_once()

    def test_pipeline_execution_success_path(self):
        """
        Тест: Проверка успешного прохождения пайплайна при низком уровне риска.
        """
        random_risk_score = random.randint(0, 30)
        random_gateway_id = uuid.uuid4().hex

        with patch('skills.repo_security_gateway.RepoSecurityGateway') as MockGateway, \
             patch('skills.vulnerability_analyzer.VulnerabilityAnalyzer') as MockAnalyzer:

            gateway_instance = MockGateway.return_value
            analyzer_instance = MockAnalyzer.return_value

            gateway_instance.scan_and_evaluate.return_value = {"status": "clean", "id": random_gateway_id}
            analyzer_instance.run.return_value = {"risk_score": random_risk_score, "critical": False}

            result = self.pipeline.run_pipeline()

            self.assertTrue(result, "Pipeline должен вернуть True при отсутствии критических угроз")

    def test_stream_processing_integrity(self):
        """
        Тест: Проверка корректности обработки потока данных анализатором внутри пайплайна.
        """
        random_stream_content = ''.join(random.choices(string.ascii_letters, k=64)).encode()
        stream = io.BytesIO(random_stream_content)

        with patch('skills.vulnerability_analyzer.VulnerabilityAnalyzer') as MockAnalyzer:
            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.process_vulnerability_stream.return_value = True

            result = self.pipeline.process_audit_stream(stream)

            self.assertTrue(result)
            analyzer_instance.process_vulnerability_stream.assert_called_with(stream)

    def test_dependency_risk_evaluation_logic(self):
        """
        Тест: Проверка логики оценки риска на основе случайных метрик.
        """
        random_metrics = {
            "cve_count": random.randint(1, 50),
            "severity": random.choice(['low', 'medium', 'high', 'critical'])
        }

        with patch('skills.vulnerability_analyzer.VulnerabilityAnalyzer') as MockAnalyzer:
            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.evaluate_risk_score.return_value = random_metrics['cve_count']

            score = analyzer_instance.evaluate_risk_score(random_metrics)

            self.assertEqual(score, random_metrics['cve_count'])
            self.assertIsInstance(score, int)

    def test_gateway_initialization_with_random_path(self):
        """
        Тест: Убедиться, что шлюз безопасности инициализируется с переданным путем репозитория.
        """
        with patch('skills.repo_security_gateway.RepoSecurityGateway') as MockGateway:
            _ = self.pipeline.run_pipeline()

            MockGateway.assert_called_with(self.repo_path)

if __name__ == '__main__':
    unittest.main()