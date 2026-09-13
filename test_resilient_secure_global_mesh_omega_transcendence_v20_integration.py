import unittest
from skills.resilient_secure_global_mesh_omega_transcendence_v20 import (
    ResilientSecureGlobalMeshOmegaTranscendenceV20,
    ResilientSecureGlobalMeshOmegaTranscendenceV20Error
)

class TestResilientSecureGlobalMeshOmegaTranscendenceV20Integration(unittest.TestCase):
    def setUp(self):
        self.mesh = ResilientSecureGlobalMeshOmegaTranscendenceV20(
            db_path=":memory:",
            max_memory_mb=128,
            calls=5,
            period=1.0,
            raise_on_limit=True
        )
        self.target = "https://www.google.com"
        self.timeout = 5

    def test_mesh_lifecycle_integration(self):
        # Проверка валидации заголовков
        is_valid = self.mesh.validate_target_headers(self.target, self.timeout)
        self.assertIsInstance(is_valid, bool)

        # Проверка координации расширения
        coord_result = self.mesh.coordinate_expansion(self.target, self.timeout)
        self.assertIsInstance(coord_result, bool)

        # Проверка безопасной координации
        safe_coord = self.mesh.coordinate_expansion_safe(self.target, self.timeout)
        self.assertIsInstance(safe_coord, bool)

        # Проверка маршрутизации
        try:
            route_data = self.mesh.route_request(self.target, self.timeout)
            self.assertIsInstance(route_data, str)
        except Exception as e:
            self.fail(f"route_request failed: {e}")

        # Проверка обработки потока
        try:
            self.mesh.process_stream(self.target, self.timeout)
        except Exception as e:
            self.fail(f"process_stream failed: {e}")

    def test_analytics_export_integration(self):
        report_data = {"status": "stable", "nodes": 42}
        self.mesh.export_analytics_report(self.target, report_data)
        
        exported = self.mesh.get_exported_report(self.target)
        self.assertEqual(exported, report_data)
        self.assertIsNot(exported, report_data)  # Проверка на копирование словаря

    def test_error_handling_compatibility(self):
        # Проверка наличия кастомного исключения
        try:
            raise ResilientSecureGlobalMeshOmegaTranscendenceV20Error("Test error")
        except ResilientSecureGlobalMeshOmegaTranscendenceV20Error:
            pass

if __name__ == "__main__":
    unittest.main()