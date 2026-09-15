import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.package_dependency_resolver import (
    PackageDependencyResolver,
    VersionConstraint,
    DependencyNode
)

class TestPackageDependencyResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = PackageDependencyResolver()
        self.random_pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_error_msg = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def test_resolve_dependencies_success(self):
        target_dep = f"dep-{uuid.uuid4().hex[:6]}"
        target_ver = f"{random.randint(1, 5)}.0.0"
        
        mock_metadata = {
            "info": {"name": self.random_pkg_name, "version": self.random_version},
            "requires_dist": [f"{target_dep} (>={target_ver})"]
        }

        with patch('skills.package_dependency_resolver.pypi_client.get_package_metadata') as mock_meta, \
             patch('skills.package_dependency_resolver.pypi_client.get_dependencies') as mock_deps:
            
            mock_meta.return_value = mock_metadata
            mock_deps.return_value = [f"{target_dep} (>={target_ver})"]

            dependency_tree = self.resolver.resolve(self.random_pkg_name, self.random_version)
            
            self.assertIsInstance(dependency_tree, dict)
            self.assertIn(self.random_pkg_name, dependency_tree)
            self.assertEqual(dependency_tree[self.random_pkg_name]["version"], self.random_version)
            self.assertIn(target_dep, dependency_tree[self.random_pkg_name]["dependencies"])

    def test_version_constraint_matching(self):
        major = random.randint(1, 5)
        minor = random.randint(0, 9)
        patch_num = random.randint(0, 9)
        
        ver_str = f"{major}.{minor}.{patch_num}"
        constraint_str = f">={major}.0.0"
        
        constraint = VersionConstraint(constraint_str)
        is_satisfied = constraint.satisfies(ver_str)
        
        self.assertTrue(is_satisfied)
        
        invalid_ver = f"{major - 1 if major > 1 else 0}.99.99"
        if invalid_ver != ver_str:
            self.assertFalse(constraint.satisfies(invalid_ver))

    def test_dependency_conflict_handling(self):
        pkg_a = f"lib-a-{uuid.uuid4().hex[:4]}"
        pkg_b = f"lib-b-{uuid.uuid4().hex[:4]}"
        shared_dep = f"shared-{uuid.uuid4().hex[:4]}"
        
        ver_1 = f"1.{random.randint(0,9)}.0"
        ver_2 = f"2.{random.randint(0,9)}.0"

        with patch('skills.package_dependency_resolver.pypi_client.get_dependencies') as mock_deps:
            def side_effect(name, ver):
                if name == self.random_pkg_name:
                    return [f"{pkg_a} (==1.0.0)", f"{pkg_b} (==1.0.0)"]
                elif name == pkg_a:
                    return [f"{shared_dep} (>={ver_1})"]
                elif name == pkg_b:
                    return [f"{shared_dep} (<{ver_2})"]
                return []

            mock_deps.side_effect = side_effect

            with self.assertRaises(Exception) as ctx:
                self.resolver.resolve(self.random_pkg_name, self.random_version)
            
            self.assertIsNotNone(ctx.exception)

    def test_parse_stream_requirements(self):
        stream_content = f"{self.random_pkg_name}=={self.random_version}\n".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        result = self.resolver.parse_stream_requirements(mock_stream)
        
        self.assertIsInstance(result, list)
        self.assertTrue(any(item.get('name') == self.random_pkg_name for item in result))

    def test_dependency_node_structure(self):
        node = DependencyNode(self.random_pkg_name, self.random_version)
        child_name = f"child-{uuid.uuid4().hex[:5]}"
        child_version = "1.2.3"
        
        node.add_child(DependencyNode(child_name, child_version))
        
        serialized = node.to_dict()
        self.assertEqual(serialized["name"], self.random_pkg_name)
        self.assertEqual(serialized["version"], self.random_version)
        self.assertEqual(len(serialized["children"]), 1)
        self.assertEqual(serialized["children"][0]["name"], child_name)

    def test_fallback_on_pypi_failure(self):
        with patch('skills.package_dependency_resolver.pypi_client.get_package_metadata') as mock_meta:
            mock_meta.side_effect = RuntimeError(self.random_error_msg)

            with self.assertRaises(RuntimeError) as ctx:
                self.resolver.resolve(self.random_pkg_name, self.random_version)
            
            self.assertIn(self.random_error_msg, str(ctx.exception))