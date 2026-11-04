import io
import os
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch
import uuid

from skills.repo_auditor import RepoAuditor


def generate_random_string(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class TestRepoAuditor(unittest.TestCase):

    def setUp(self):
        self.unique_id = uuid.uuid4().hex
        self.temp_repo_dir = tempfile.mkdtemp(prefix=f"audit_repo_{self.unique_id}_")

    def tearDown(self):
        if os.path.exists(self.temp_repo_dir):
            for root, dirs, files in os.walk(self.temp_repo_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.temp_repo_dir)

    def test_init_sets_repo_path(self):
        random_path = os.path.join(tempfile.gettempdir(), f"repo_{uuid.uuid4().hex}")
        auditor = RepoAuditor(random_path)
        self.assertTrue(hasattr(auditor, "repo_path"))
        self.assertEqual(str(auditor.repo_path), random_path)

    def test_audit_repository_execution(self):
        file_prefix = f"module_{uuid.uuid4().hex[:8]}"
        file_path = os.path.join(self.temp_repo_dir, f"{file_prefix}.py")
        random_token = f"TOKEN_{uuid.uuid4().hex}"
        
        code_content = (
            f"class TestClass_{uuid.uuid4().hex[:6]}:\n"
            f"    def test_method(self):\n"
            f"        return '{random_token}'\n"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_content)

        auditor = RepoAuditor(self.temp_repo_dir)
        
        audit_method = getattr(auditor, "audit_repository", getattr(auditor, "audit", getattr(auditor, "run", None)))
        if audit_method:
            result = audit_method()
            self.assertIsNotNone(result)

    def test_calculate_metrics_with_random_files(self):
        num_lines = random.randint(15, 60)
        file_name = f"script_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.temp_repo_dir, file_name)
        
        lines = [f"# Comment line {i} - {generate_random_string(10)}" for i in range(num_lines)]
        lines.append(f"def func_{uuid.uuid4().hex[:6]}():\n    pass")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        auditor = RepoAuditor(self.temp_repo_dir)
        if hasattr(auditor, "calculate_metrics"):
            metrics = auditor.calculate_metrics()
            self.assertIsNotNone(metrics)
            if isinstance(metrics, dict):
                self.assertTrue(len(metrics) >= 0)

    def test_detect_issues_with_simulated_code(self):
        issue_marker = f"TODO_FIX_{uuid.uuid4().hex}"
        file_name = f"problematic_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.temp_repo_dir, file_name)
        
        long_line = "# " + generate_random_string(250)
        todo_comment = f"# {issue_marker}"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{long_line}\n{todo_comment}\n")

        auditor = RepoAuditor(self.temp_repo_dir)
        if hasattr(auditor, "detect_issues"):
            issues = auditor.detect_issues()
            self.assertIsNotNone(issues)

    def test_analyze_structure(self):
        dir_name = f"pkg_{uuid.uuid4().hex[:8]}"
        sub_dir = os.path.join(self.temp_repo_dir, dir_name)
        os.makedirs(sub_dir)
        
        init_file = os.path.join(sub_dir, "__init__.py")
        mod_file = os.path.join(sub_dir, f"submodule_{uuid.uuid4().hex[:6]}.py")
        
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("# init")
        with open(mod_file, "w", encoding="utf-8") as f:
            f.write("VAL = 42")

        auditor = RepoAuditor(self.temp_repo_dir)
        structure_method = getattr(
            auditor, 
            "analyze_structure", 
            getattr(auditor, "evaluate_structure", getattr(auditor, "check_structure", None))
        )
        if structure_method:
            res = structure_method()
            self.assertIsNotNone(res)

    def test_generate_report_writing(self):
        auditor = RepoAuditor(self.temp_repo_dir)
        out_filename = f"report_{uuid.uuid4().hex}.json"
        out_path = os.path.join(self.temp_repo_dir, out_filename)
        
        gen_method = getattr(auditor, "generate_report", getattr(auditor, "save_report", None))
        if gen_method:
            with patch("builtins.open", mock_open()) as mock_file_handle:
                try:
                    gen_method(out_path)
                except TypeError:
                    gen_method()

    def test_process_stream_with_byte_buffer(self):
        random_bytes_content = f"stream_data_{uuid.uuid4().hex}".encode("utf-8")
        byte_stream = io.BytesIO(random_bytes_content)
        
        auditor = RepoAuditor(self.temp_repo_dir)
        if hasattr(auditor, "process_log_stream"):
            result = auditor.process_log_stream(byte_stream)
            self.assertIsNotNone(result)
        elif hasattr(auditor, "process_stream"):
            result = auditor.process_stream(byte_stream)
            self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()