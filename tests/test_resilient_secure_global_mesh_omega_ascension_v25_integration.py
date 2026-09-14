import unittest
from skills.resilient_secure_global_mesh_omega_ascension_v25 import ResilientSecureGlobalMeshOmegaAscensionV25

class TestResilientSecureGlobalMeshOmegaAscensionV25Integration(unittest.TestCase):
    def setUp(self):
        self.mesh_node = ResilientSecureGlobalMeshOmegaAscensionV25(
            db_path=":memory:",
            max_memory_mb=128,
            calls=5,
            period=1.0,
            raise_on_limit=False
        )
        self.test_url = "https://www.google.com"

    def test_full_mesh_integration_lifecycle(self):
        # 1. Проверка валидации заголовков через Genesis
        is_valid = self.mesh_node.validate_target_headers(self.test_url, timeout=5)
        self.assertIsInstance(is_valid, bool)

        # 2. Проверка координации расширения (Transcendence)
        is_coordinated = self.mesh_node.coordinate_expansion(self.test_url, timeout=5)
        self.assertIsInstance(is_coordinated, bool)

        # 3. Проверка маршрутизации запроса
        route_data = self.mesh_node.route_request(self.test_url, timeout=5)
        self.assertIsInstance(route_data, str)
        self.assertGreater(len(route_data), 0)

        # 4. Проверка обработки потока
        stream_result = self.mesh_node.process_stream(self.test_url, timeout=5)
        self.assertIsNone(stream_result)

        # 5. Проверка аналитического отчета (внутреннее состояние)
        report_payload = {"status": "active", "node": "v25"}
        self.mesh_node.export_analytics_report(self.test_url, report_payload)
        exported = self.mesh_node.get_exported_report(self.test_url)

        self.assertIsInstance(exported, dict)
        self.assertEqual(exported.get("status"), "active")

    def test_genesis_transcendence_dependency_instantiation(self):
        # Проверка корректности инициализации зависимых модулей
        self.assertIsNotNone(self.mesh_node.genesis_module)
        self.assertIsNotNone(self.mesh_node.transcendence_module)

        # Проверка наличия атрибутов, унаследованных от Genesis/Transcendence
        self.assertTrue(hasattr(self.mesh_node.genesis_module, "db_path"))
        self.assertTrue(hasattr(self.mesh_node.transcendence_module, "db_path"))

if __name__ == "__main__":
    unittest.main()