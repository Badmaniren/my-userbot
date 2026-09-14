import unittest
from skills.resilient_secure_global_mesh_omega_transcendence_v20 import (
    ResilientSecureGlobalMeshOmegaTranscendenceV20,
    ResilientSecureGlobalMeshOmegaTranscendenceV20Error,
    ResilientSecureGlobalMeshomegaTranscendenceV20Error
)

class TestResilientSecureGlobalMeshOmegaTranscendenceV20Integration(unittest.TestCase):
    def setUp(self):
        self.mesh = ResilientSecureGlobalMeshOmegaTranscendenceV20(
            db_path=":memory:",
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_exception_aliases(self):
        self.assertTrue(issubclass(ResilientSecureGlobalMeshomegaTranscendenceV20Error, Exception))
        self.assertIs(ResilientSecureGlobalMeshOmegaTranscendenceV20Error, ResilientSecureGlobalMeshomegaTranscendenceV20Error)

    def test_analytics_export_and_retrieve(self):
        target = "http://example.com/api/v1"
        report_data = {"status": "transcended", "nodes": 49}

        self.mesh.export_analytics_report(target, report_data)
        exported = self.mesh.get_exported_report(target)

        self.assertIsInstance(exported, dict)
        self.assertEqual(exported.get("status"), "transcended")
        self.assertEqual(exported.get("nodes"), 49)

    def test_validation_and_expansion_signatures(self):
        target = "http://invalid-nonexistent-domain-test.local"

        is_valid_headers = self.mesh.validate_target_headers(target, timeout=1)
        self.assertIsInstance(is_valid_headers, bool)

        expansion = self.mesh.coordinate_expansion(target, timeout=1)
        self.assertIsInstance(expansion, bool)

        expansion_safe = self.mesh.coordinate_expansion_safe(target, timeout=1)
        self.assertIsInstance(expansion_safe, bool)

if __name__ == "__main__":
    unittest.main()