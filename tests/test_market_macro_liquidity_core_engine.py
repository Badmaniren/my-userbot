import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_macro_liquidity_core_engine import start_new, MacroLiquidityCoreEngine

class TestMarketMacroLiquidityCoreEngine(unittest.TestCase):

    def test_start_new_success(self):
        service_url = f"https://{uuid.uuid4().hex}.com/api/{uuid.uuid4().hex}"
        expected_json = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_dep = MagicMock()
        mock_dependencies = {
            uuid.uuid4().hex: mock_dep
        }

        with patch("skills.market_macro_liquidity_core_engine.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_json
            mock_get.return_value = mock_response

            result = start_new(service_url, mock_dependencies)

            mock_get.assert_called_once_with(service_url)
            self.assertEqual(result, expected_json)

    def test_start_new_exception_handling(self):
        service_url = f"https://{uuid.uuid4().hex}.com/api/{uuid.uuid4().hex}"
        mock_dependencies = {
            "db_storage": uuid.uuid4().hex
        }

        with self.assertRaises(TypeError):
            start_new(service_url, mock_dependencies)

    def test_macro_liquidity_core_engine_process(self):
        engine = MacroLiquidityCoreEngine()
        test_id = uuid.uuid4().hex
        payload = {
            "test_id": test_id,
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        result = engine.process_macro_liquidity_data(payload)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("processed_id"), test_id)

if __name__ == "__main__":
    unittest.main()