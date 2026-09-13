import unittest
import os
from skills.resilient_secure_global_mesh_omega_singularity_v40 import ResilientSecureGlobalMeshOmegaSingularityV40
from skills.resilient_secure_global_mesh_omega_singularity_v39 import ResilientSecureGlobalMeshOmegaSingularityV39
from skills.resilient_secure_global_mesh_omega_transcendence_v32 import ResilientSecureGlobalMeshOmegaTranscendenceV32

class TestResilientSecureGlobalMeshOmegaSingularityV40(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_mesh_v40.db"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 60
        self.raise_on_limit = True
        self.target_url = "https://example.com"
        self.timeout = 5
        
        self.mesh_v40 = ResilientSecureGlobalMeshOmegaSingularityV40(
            self.db_path, self.max_memory_mb, self.calls, self.period, self.raise_on_limit
        )
        self.mesh_v39 = ResilientSecureGlobalMeshOmegaSingularityV39(
            self.db_path, self.max_memory_mb, self.calls, self.period, self.raise_on_limit
        )
        self.mesh_v32 = ResilientSecureGlobalMeshOmegaTranscendenceV32(
            self.db_path, self.max_memory_mb, self.calls, self.period, self.raise_on_limit
        )

    def test_integration_composition_flow(self):
        # Проверка валидации заголовков через основной модуль
        is_valid = self.mesh_v40.validate_target_headers(self.target_url, self.timeout)
        self.assertIsInstance(is_valid, bool)

        # Проверка координации расширения (безопасный метод)
        expansion_result = self.mesh_v40.coordinate_expansion_safe(self.target_url, self.timeout)
        self.assertIsInstance(expansion_result, bool)

        # Проверка маршрутизации
        route = self.mesh_v40.route_request(self.target_url, self.timeout)
        self.assertIsInstance(route, str)

        # Проверка аналитического отчета
        report_data = {"status": "stable", "version": "v40"}
        self.mesh_v40.export_analytics_report(self.target_url, report_data)
        exported = self.mesh_v40.get_exported_report(self.target_url)
        self.assertEqual(exported.get("version"), "v40")

    def test_cross_version_compatibility(self):
        # Проверка, что v40 корректно взаимодействует с данными, 
        # которые могли быть созданы v39 или v32
        data_v39 = {"node": "v39_legacy"}
        self.mesh_v39.export_analytics_report(self.target_url, data_v39)
        
        report_from_v40 = self.mesh_v40.get_exported_report(self.target_url)
        self.assertEqual(report_from_v40.get("node"), "v39_legacy")

        data_v32 = {"node": "v32_legacy"}
        self.mesh_v32.export_analytics_report(self.target_url, data_v32)
        
        report_from_v40_v32 = self.mesh_v40.get_exported_report(self.target_url)
        self.assertEqual(report_from_v40_v32.get("node"), "v32_legacy")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

if __name__ == '__main__':
    unittest.main()