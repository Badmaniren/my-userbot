import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_global_mesh_gateway_v11 import (
    ResilientSecureGlobalMeshGatewayV11,
    ResilientSecureGlobalMeshGatewayV11Error,
)
from skills.resilient_secure_global_mesh_federation_v10 import ResilientSecureGlobalMeshFederationV10
from skills.resilient_secure_smart_crawler_hub_v11_global_mesh import ResilientSecureSmartCrawlerHubV11GlobalMesh


class TestResilientSecureGlobalMeshGatewayV11(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 256
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        
        self.gateway = ResilientSecureGlobalMeshGatewayV11(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_initialization_composition(self):
        self.assertIsInstance(self.gateway.federation_node, ResilientSecureGlobalMeshFederationV10)
        self.assertIsInstance(self.gateway.mesh_hub_node, ResilientSecureSmartCrawlerHubV11GlobalMesh)

    def test_validate_target_headers_success(self):
        target = "http://example.com"
        timeout = 5
        
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            result = self.gateway.validate_target_headers(target, timeout)
            self.assertTrue(result)

    def test_validate_target_headers_failure(self):
        target = "http://example.com"
        timeout = 5
        
        with patch('requests.head') as mock_head:
            mock_head.side_effect = Exception("Connection error")
            
            result = self.gateway.validate_target_headers(target, timeout)
            self.assertFalse(result)

    def test_coordinate_expansion(self):
        target = "http://example.com"
        timeout = 5
        
        with patch.object(self.gateway.mesh_hub_node, 'coordinate_expansion', return_value=True) as mock_coord:
            result = self.gateway.coordinate_expansion(target, timeout)
            self.assertTrue(result)
            mock_coord.assert_called_once_with(target, timeout)

    def test_coordinate_expansion_safe_success(self):
        target = "http://example.com"
        timeout = 5
        
        with patch.object(self.gateway, 'coordinate_expansion', return_value=True) as mock_coord:
            result = self.gateway.coordinate_expansion_safe(target, timeout)
            self.assertTrue(result)

    def test_coordinate_expansion_safe_failure(self):
        target = "http://example.com"
        timeout = 5
        
        with patch.object(self.gateway, 'coordinate_expansion', side_effect=Exception("Expansion failed")):
            result = self.gateway.coordinate_expansion_safe(target, timeout)
            self.assertFalse(result)

    def test_export_and_get_exported_report(self):
        target = "http://example.com"
        report_data = {"status": "active", "nodes": 42}
        
        with patch.object(self.gateway.mesh_hub_node, 'export_analytics_report') as mock_export, \
             patch.object(self.gateway.mesh_hub_node, 'get_exported_report', return_value=report_data) as mock_get:
            
            self.gateway.export_analytics_report(target, report_data)
            mock_export.assert_called_once_with(target, report_data)
            
            retrieved = self.gateway.get_exported_report(target)
            self.assertEqual(retrieved, report_data)
            mock_get.assert_called_once_with(target)

    def test_process_stream(self):
        target = "http://example.com/stream"
        timeout = 5
        
        with patch.object(self.gateway.mesh_hub_node, 'process_stream') as mock_process:
            self.gateway.process_stream(target, timeout)
            mock_process.assert_called_once_with(target, timeout)

    def test_route_request(self):
        target = "http://example.com/route"
        timeout = 5
        
        with patch.object(self.gateway.federation_node, 'route_request', return_value={"routed": True}) as mock_route:
            result = self.gateway.route_request(target, timeout)
            self.assertEqual(result, {"routed": True})
            mock_route.assert_called_once_with(target, timeout)


if __name__ == '__main__':
    unittest.main()