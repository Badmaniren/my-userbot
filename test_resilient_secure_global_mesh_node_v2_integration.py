import unittest
from skills.resilient_secure_global_mesh_node_v2 import ResilientSecureGlobalMeshNodeV2, ResilientSecureGlobalMeshNodeV2Error

class TestResilientSecureGlobalMeshNodeV2Integration(unittest.TestCase):
    def setUp(self):
        self.node = ResilientSecureGlobalMeshNodeV2(
            db_path=":memory:",
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_inheritance_and_composition(self):
        self.assertIsNotNone(self.node.analytics_exporter)
        self.assertTrue(hasattr(self.node, 'coordinate_expansion'))
        self.assertTrue(hasattr(self.node, 'validate_target_headers'))

    def test_analytics_export_and_retrieval(self):
        target = "https://example.com/mesh-node"
        report_data = {"status": "active", "load": 0.42}
        
        self.node.export_analytics_report(target, report_data)
        retrieved_report = self.node.get_exported_report(target)
        
        self.assertEqual(retrieved_report, report_data)

    def test_coordinate_expansion_safe_with_invalid_url(self):
        invalid_url = "http://invalid-mesh-node-url-99999.local"
        result = self.node.coordinate_expansion_safe(url=invalid_url, timeout=1)
        self.assertFalse(result)

    def test_exception_exists(self):
        with self.assertRaises(ResilientSecureGlobalMeshNodeV2Error):
            raise ResilientSecureGlobalMeshNodeV2Error("Test error")

if __name__ == "__main__":
    unittest.main()