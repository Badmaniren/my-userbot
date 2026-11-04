import unittest
import uuid
import random
import os
import tempfile
import shutil
import io

class TestDependencyScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix=f"repo_{uuid.uuid4().hex}_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _generate_pkg_name(self):
        chars = "abcdefghijklmnopqrstuvwxyz"
        prefix = "".join(random.choice(chars) for _ in range(random.randint(4, 8)))
        suffix = uuid.uuid4().hex[:6]
        return f"{prefix}-{suffix}"

    def _generate_version(self):
        return f"{random.randint(1, 9)}.{random.randint(0, 20)}.{random.randint(0, 50)}"

    def test_init_sets_repo_path(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)
        self.assertEqual(scanner.repo_path, self.test_dir)

    def test_scan_finds_dependency_files(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)

        sub_dir = os.path.join(self.test_dir, f"sub_{uuid.uuid4().hex[:8]}")
        os.makedirs(sub_dir)

        req_path = os.path.join(self.test_dir, "requirements.txt")
        setup_path = os.path.join(sub_dir, "setup.py")
        pyproject_path = os.path.join(self.test_dir, "pyproject.toml")
        random_file_path = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.txt")

        for p in [req_path, setup_path, pyproject_path, random_file_path]:
            with open(p, "w", encoding="utf-8") as f:
                f.write(uuid.uuid4().hex)

        found_files = scanner.find_dependency_files()
        self.assertIn(req_path, found_files)
        self.assertIn(setup_path, found_files)
        self.assertIn(pyproject_path, found_files)
        self.assertNotIn(random_file_path, found_files)

    def test_parse_requirements_txt(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)

        pkg_1 = self._generate_pkg_name()
        ver_1 = self._generate_version()
        pkg_2 = self._generate_pkg_name()
        ver_2 = self._generate_version()
        pkg_3 = self._generate_pkg_name()

        comment_salt = uuid.uuid4().hex
        content = (
            f"# Comment {comment_salt}\n"
            f"{pkg_1}=={ver_1}\n"
            f"\n"
            f"   \n"
            f"{pkg_2}>={ver_2} # inline comment\n"
            f"{pkg_3}\n"
        )

        req_file = os.path.join(self.test_dir, f"req_{uuid.uuid4().hex[:6]}.txt")
        with open(req_file, "w", encoding="utf-8") as f:
            f.write(content)

        parsed = scanner.parse_requirements(req_file)

        self.assertIsInstance(parsed, dict)
        self.assertIn(pkg_1, parsed)
        self.assertEqual(parsed[pkg_1], f"=={ver_1}")
        self.assertIn(pkg_2, parsed)
        self.assertEqual(parsed[pkg_2], f">={ver_2}")
        self.assertIn(pkg_3, parsed)
        self.assertEqual(parsed[pkg_3], "*")

    def test_parse_setup_py_install_requires(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)

        pkg_a = self._generate_pkg_name()
        ver_a = self._generate_version()
        pkg_b = self._generate_pkg_name()
        ver_b = self._generate_version()

        setup_content = (
            "from setuptools import setup\n"
            f"setup(name='{uuid.uuid4().hex}',\n"
            f"      install_requires=['{pkg_a}=={ver_a}', '{pkg_b}>={ver_b}'])\n"
        )

        setup_file = os.path.join(self.test_dir, "setup.py")
        with open(setup_file, "w", encoding="utf-8") as f:
            f.write(setup_content)

        parsed = scanner.parse_setup_py(setup_file)

        self.assertIsInstance(parsed, dict)
        self.assertIn(pkg_a, parsed)
        self.assertEqual(parsed[pkg_a], f"=={ver_a}")
        self.assertIn(pkg_b, parsed)
        self.assertEqual(parsed[pkg_b], f">={ver_b}")

    def test_parse_pyproject_toml_dependencies(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)

        pkg_x = self._generate_pkg_name()
        ver_x = self._generate_version()
        pkg_y = self._generate_pkg_name()
        ver_y = self._generate_version()

        toml_content = (
            "[project]\n"
            f"name = \"{uuid.uuid4().hex}\"\n"
            "dependencies = [\n"
            f"    \"{pkg_x}=={ver_x}\",\n"
            f"    \"{pkg_y}>={ver_y}\"\n"
            "]\n"
        )

        pyproject_file = os.path.join(self.test_dir, "pyproject.toml")
        with open(pyproject_file, "w", encoding="utf-8") as f:
            f.write(toml_content)

        parsed = scanner.parse_pyproject_toml(pyproject_file)

        self.assertIsInstance(parsed, dict)
        self.assertIn(pkg_x, parsed)
        self.assertEqual(parsed[pkg_x], f"=={ver_x}")
        self.assertIn(pkg_y, parsed)
        self.assertEqual(parsed[pkg_y], f">={ver_y}")

    def test_normalize_package_names(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)

        raw_name = f"TeSt_PkG.{uuid.uuid4().hex[:6]}"
        expected_name = raw_name.lower().replace("_", "-").replace(".", "-")

        normalized = scanner.normalize_name(raw_name)
        self.assertEqual(normalized, expected_name)

    def test_scan_and_aggregate_dependencies(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)

        pkg_req = self._generate_pkg_name()
        ver_req = self._generate_version()
        pkg_toml = self._generate_pkg_name()
        ver_toml = self._generate_version()

        req_path = os.path.join(self.test_dir, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(f"{pkg_req}=={ver_req}\n")

        toml_path = os.path.join(self.test_dir, "pyproject.toml")
        with open(toml_path, "w", encoding="utf-8") as f:
            f.write(f"[project]\ndependencies = [\"{pkg_toml}=={ver_toml}\"]\n")

        aggregated = scanner.scan()

        self.assertIsInstance(aggregated, dict)
        normalized_req = scanner.normalize_name(pkg_req)
        normalized_toml = scanner.normalize_name(pkg_toml)

        self.assertIn(normalized_req, aggregated)
        self.assertEqual(aggregated[normalized_req], f"=={ver_req}")
        self.assertIn(normalized_toml, aggregated)
        self.assertEqual(aggregated[normalized_toml], f"=={ver_toml}")

    def test_parse_from_stream(self):
        from skills.dependency_scanner import DependencyScanner
        scanner = DependencyScanner(repo_path=self.test_dir)

        pkg = self._generate_pkg_name()
        ver = self._generate_version()
        stream_content = f"{pkg}=={ver}\n".encode("utf-8")
        stream = io.BytesIO(stream_content)

        parsed = scanner.parse_requirements_stream(stream)
        self.assertIn(pkg, parsed)
        self.assertEqual(parsed[pkg], f"=={ver}")

if __name__ == "__main__":
    unittest.main()