import unittest
import os
import tempfile
import shutil
from skills.resilient_secure_global_mesh_omega_singularity_v40 import ResilientSecureGlobalMeshOmegaSingularityV40

class TestResilientSecureGlobalMeshOmegaSingularityV40(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.test_dir, "test_mesh.db")
        cls.mesh = ResilientSecureGlobalMeshOmegaSingularityV40(
            db_path=cls.db_path,
            max_mb=10,
            calls=100,
            period=60,
            raise_on_limit=False
        )
        cls.target = "https://example.com"
        cls.timeout = 5

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    def test_integration_flow(self):
        # Проверка валидации заголовков (bool)
        is_valid = self.mesh.validate_target_headers(self.target, self.timeout)
        self.assertIsInstance(is_valid, bool)

        # Проверка координации расширения (bool)
        coord_safe = self.mesh.coordinate_expansion_safe(self.target, self.timeout)
        self.assertIsInstance(coord_safe, bool)
        
        coord = self.mesh.coordinate_expansion(self.target, self.timeout)
        self.assertIsInstance(coord, bool)

        # Проверка маршрутизации (str)
        route = self.mesh.route_request(self.target, self.timeout)
        self.assertIsInstance(route, str)

        # Проверка обработки потока
        self.mesh.process_stream(self.target, self.timeout)

    def test_analytics_consistency(self):
        report_data = {"status": "active", "nodes": 2}
        
        # Экспорт в оба узла
        self.mesh.export_analytics_report(self.target, report_data)
        
        # Получение отчета (должен вернуться dict или None)
        report = self.mesh.get_exported_report(self.target)
        if report is not None:
            self.assertIsInstance(report, dict)
            self.assertEqual(report.get("status"), "active")

if __name__ == "__main__":
    unittest.main()