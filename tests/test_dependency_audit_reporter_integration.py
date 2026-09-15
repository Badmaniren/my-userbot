import unittest
import uuid
import random
import os
import tempfile
from skills.dependency_audit_reporter import DependencyAuditReporter
from skills.vulnerability_scanner import VulnerabilityScanner
from skills.package_requirement_reader import PyPIClient
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.auto_patch_pipeline import PipelineResult as AutoPatchPipelineResult

class TestDependencyAuditReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.reporter = DependencyAuditReporter()
        self.scanner = VulnerabilityScanner()
        self.pypi_client = PyPIClient(base_url="https://pypi.org/pypi")
        self.recovery_hub = ErrorRecoveryHub()
        self.random_pkg_id = f"test-pkg-{uuid.uuid4()}"
        self.random_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_audit_and_report_generation(self):
        target_package = self.random_pkg_id
        target_version = self.random_version

        try:
            metadata = self.pypi_client.get_package_metadata(target_package, target_version)
        except Exception as e:
            metadata = {"name": target_package, "version": target_version, "error": str(e)}

        scan_result = self.scanner.scan_dependency(target_package, target_version) if hasattr(self.scanner, "scan_dependency") else {"status": "scanned", "package": target_package}

        report_payload = {
            "epic_id": str(uuid.uuid4()),
            "package": target_package,
            "version": target_version,
            "metadata": metadata,
            "scan_data": scan_result,
            "metrics": {
                "risk_score": random.uniform(0.0, 10.0),
                "vulnerabilities_found": random.randint(0, 5)
            }
        }

        report_path = os.path.join(self.temp_dir.name, f"audit_report_{uuid.uuid4()}.json")
        
        generation_result = self.reporter.generate_epic_report(report_payload, output_path=report_path)

        self.assertTrue(os.path.exists(report_path), "Интеграционный тест не смог обнаружить сгенерированный файл отчета аудита.")
        
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(target_package, content, "В сгенерированном отчете отсутствуют данные о тестируемом пакете.")

        if report_payload["metrics"]["vulnerabilities_found"] > 0:
            dummy_exception = ValueError(f"Vulnerability limit exceeded for {target_package}")
            incident = self.recovery_hub.analyze_and_recover(
                module_name="dependency_audit_reporter",
                exception=dummy_exception,
                context=report_payload
            )
            self.assertIsInstance(incident, AutoPatchPipelineResult)

if __name__ == "__main__":
    unittest.main()