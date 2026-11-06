import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.repo_health_analyzer import RepoHealthAnalyzer

class TestRepoHealthAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = RepoHealthAnalyzer()

    def test_analyze_repository_success(self):
        repo_name = f"repo_{uuid.uuid4().hex}"
        branch_name = f"branch_{uuid.uuid4().hex}"
        random_score = random.randint(1, 100)
        
        mock_audit_result = {
            "repository": repo_name,
            "branch": branch_name,
            "health_score": random_score,
            "vulnerabilities": [],
            "outdated_dependencies": random.randint(0, 10),
            "config_status": "optimal"
        }

        with patch("skills.repo_health_analyzer.RepoHealthAnalyzer._run_audit_pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_audit_result
            result = self.analyzer.analyze(repo_name, branch=branch_name)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["repository"], repo_name)
            self.assertEqual(result["branch"], branch_name)
            self.assertEqual(result["health_score"], random_score)
            mock_pipeline.assert_called_once_with(repo_name, branch_name)

    def test_analyze_repository_missing_config_raises_exception(self):
        invalid_repo = f"bad_repo_{uuid.uuid4().hex}"
        error_msg = f"Critical config missing in {invalid_repo}"

        with patch("skills.repo_health_analyzer.RepoHealthAnalyzer._run_audit_pipeline") as mock_pipeline:
            mock_pipeline.side_effect = ValueError(error_msg)
            
            with self.assertRaises(ValueError) as ctx:
                self.analyzer.analyze(invalid_repo)
            
            self.assertIn(invalid_repo, str(ctx.exception))

    def test_dependency_health_stream_parsing(self):
        random_dependency_id = uuid.uuid4().hex
        random_version = f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}"
        file_content = f"dependency_name={random_dependency_id}\nversion={random_version}\n".encode('utf-8')
        
        mock_stream = io.BytesIO(file_content)

        with patch("skills.repo_health_analyzer.open", return_value=mock_stream, create=True):
            dependency_data = self.analyzer.parse_dependency_stream(f"path_{uuid.uuid4().hex}")

            self.assertIsInstance(dependency_data, dict)
            self.assertEqual(dependency_data.get("dependency_name"), random_dependency_id)
            self.assertEqual(dependency_data.get("version"), random_version)

    def test_health_automator_integration_failure(self):
        component_name = f"automator_{uuid.uuid4().hex}"
        failure_code = random.randint(500, 599)

        with patch("skills.repo_health_analyzer.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = failure_code
            mock_response.raise_for_status.side_effect = Exception(f"HTTP Error {failure_code}")
            mock_post.return_value = mock_response

            with self.assertRaises(Exception) as ctx:
                self.analyzer.trigger_automator(component_name, payload={"token": uuid.uuid4().hex})

            self.assertIn(str(failure_code), str(ctx.exception))
            mock_post.assert_called_once()

    def test_vulnerability_analyzer_random_feed(self):
        cve_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 99999)}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        mock_vulnerability_payload = {
            "vulnerability_id": cve_id,
            "severity": severity,
            "package": f"pkg_{uuid.uuid4().hex}"
        }

        with patch("skills.repo_health_analyzer.vulnerability_analyzer") as mock_vuln_mod:
            mock_vuln_mod.scan.return_value = mock_vulnerability_payload
            
            audit_report = self.analyzer.audit_vulnerabilities(uuid.uuid4().hex)

            self.assertEqual(audit_report["vulnerability_id"], cve_id)
            self.assertEqual(audit_report["severity"], severity)
            mock_vuln_mod.scan.assert_called_once()

if __name__ == "__main__":
    unittest.main()