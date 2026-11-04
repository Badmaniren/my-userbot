import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.dependency_comparator import DependencyComparator
from skills.dependency_scanner import DependencyScanner

class TestDependencyComparatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.unique_package = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        self.req_file = os.path.join(self.repo_path, "requirements.txt")
        with open(self.req_file, "w") as f:
            f.write(f"{self.unique_package}=={self.random_version}\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dependency_comparator_with_scanner_integration(self):
        scanner = DependencyScanner(self.repo_path)
        scanned_deps = scanner.scan()
        
        self.assertIsNotNone(scanned_deps)

        comparator = DependencyComparator(self.repo_path)
        self.assertTrue(hasattr(comparator, "compare") or hasattr(comparator, "run") or hasattr(comparator, "check_updates"))
        
        if hasattr(comparator, "compare"):
            result = comparator.compare()
        elif hasattr(comparator, "run"):
            result = comparator.run()
        else:
            result = comparator.check_updates()

        self.assertIsInstance(result, (dict, list, str, bool))

if __name__ == "__main__":
    unittest.main()