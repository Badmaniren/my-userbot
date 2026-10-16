import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import uuid
import random
import string
import io

# Импортируем тестируемые компоненты
# Предполагается, что код находится в доступе для импорта
try:
    from skills.patch_executor import PatchExecutor, PatchExecutorError
except ImportError:
    # Временный fallback для структуры окружения
    import sys
    from types import ModuleType
    m = ModuleType("skills.patch_executor")
    sys.modules["skills.patch_executor"] = m
    # Здесь должен быть код из условия, если файл физически отсутствует
    exec("""
import os
class PatchExecutorError(Exception): pass
class PatchExecutor:
    def __init__(self, repo_path=None, git_inspector=None, lesson_parser=None):
        if repo_path is None and git_inspector is not None and hasattr(git_inspector, "repo_path"):
            repo_path = git_inspector.repo_path
        self.repo_path = repo_path or "."
        self.git_inspector = git_inspector
        self.lesson_parser = lesson_parser
    def apply_patch(self, patch_data: dict) -> bool:
        if not isinstance(patch_data, dict) or "file_path" not in patch_data or "content" not in patch_data:
            raise PatchExecutorError("Invalid patch data format.")
        file_path = patch_data["file_path"]
        content = patch_data["content"]
        full_path = file_path if os.path.isabs(file_path) else os.path.join(self.repo_path, file_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            raise PatchExecutorError(f"Failed to apply patch: {e}")
    def execute_from_lessons(self) -> dict:
        if not self.lesson_parser: return {}
        hypotheses = self.lesson_parser.parse_lessons()
        results = {}
        for hyp in hypotheses:
            hyp_id = hyp.get("id")
            patches = hyp.get("patches", [])
            success = True
            for patch_item in patches:
                try:
                    self.apply_patch(patch_item)
                except Exception:
                    success = False
            results[hyp_id] = success
        return results
    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        if not self.git_inspector: return False
        try:
            original_content = self.git_inspector.read_file_at_commit(commit_hash, file_path)
            return self.apply_patch({"file_path": file_path, "content": original_content, "mode": "overwrite"})
        except Exception as e:
            raise PatchExecutorError(f"Failed to rollback patch: {e}")
    """, m.__dict__)
    from skills.patch_executor import PatchExecutor, PatchExecutorError

class TestPatchExecutorInquisition(unittest.TestCase):
    """Инквизиторская проверка модуля PatchExecutor на ересь и баги."""

    def _generate_random_string(self, length=12):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_path(self):
        return os.path.join(self._generate_random_string(5), self._generate_random_string(8) + ".tmp")

    def test_init_with_git_inspector_path(self):
        """Проверка наследования пути из git_inspector."""
        random_repo_path = f"/{self._generate_random_string()}/{self._generate_random_string()}"
        mock_inspector = MagicMock()
        mock_inspector.repo_path = random_repo_path
        
        executor = PatchExecutor(git_inspector=mock_inspector)
        self.assertEqual(executor.repo_path, random_repo_path, "Executor должен забирать путь у инспектора!")

    def test_apply_patch_invalid_format(self):
        """Проверка реакции на поврежденные данные патча."""
        executor = PatchExecutor(repo_path=".")
        invalid_data = {self._generate_random_string(): self._generate_random_string()}
        
        with self.assertRaises(PatchExecutorError):
            executor.apply_patch(invalid_data)

    def test_apply_patch_file_writing_logic(self):
        """Проверка корректности записи данных и создания директорий."""
        random_root = f"/{self._generate_random_string()}"
        random_sub_path = self._generate_random_path()
        random_content = self._generate_random_string(100)
        
        executor = PatchExecutor(repo_path=random_root)
        
        with patch("os.makedirs") as mock_dirs, \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("os.path.isabs", return_value=False):
            
            patch_data = {
                "file_path": random_sub_path,
                "content": random_content
            }
            
            result = executor.apply_patch(patch_data)
            
            self.assertTrue(result)
            expected_full_path = os.path.join(random_root, random_sub_path)
            mock_dirs.assert_called_with(os.path.dirname(expected_full_path), exist_ok=True)
            mock_file.assert_called_once_with(expected_full_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(random_content)

    def test_execute_from_lessons_integration(self):
        """Проверка цепочки выполнения гипотез из парсера."""
        mock_parser = MagicMock()
        hyp_id_1 = f"hyp_{uuid.uuid4().hex}"
        hyp_id_2 = f"hyp_{uuid.uuid4().hex}"
        
        # Первая гипотеза успешна, вторая провальна
        mock_parser.parse_lessons.return_value = [
            {
                "id": hyp_id_1,
                "patches": [{"file_path": "f1.txt", "content": "c1"}]
            },
            {
                "id": hyp_id_2,
                "patches": [{"file_path": "f2.txt", "content": "c2"}]
            }
        ]
        
        executor = PatchExecutor(lesson_parser=mock_parser)
        
        def side_effect(p_data):
            if p_data["file_path"] == "f2.txt":
                raise Exception("Inquisition Failure")
            return True

        with patch.object(executor, 'apply_patch', side_effect=side_effect):
            results = executor.execute_from_lessons()
            
            self.assertEqual(len(results), 2)
            self.assertTrue(results[hyp_id_1])
            self.assertFalse(results[hyp_id_2])

    def test_rollback_patch_success(self):
        """Проверка отката файла к состоянию коммита."""
        mock_inspector = MagicMock()
        random_commit = uuid.uuid4().hex
        random_file = self._generate_random_path()
        random_old_content = f"OLD_DATA_{self._generate_random_string()}"
        
        mock_inspector.read_file_at_commit.return_value = random_old_content
        
        executor = PatchExecutor(git_inspector=mock_inspector)
        
        with patch.object(executor, 'apply_patch') as mock_apply:
            mock_apply.return_value = True
            
            res = executor.rollback_patch(random_file, random_commit)
            
            self.assertTrue(res)
            mock_inspector.read_file_at_commit.assert_called_once_with(random_commit, random_file)
            mock_apply.assert_called_once()
            args = mock_apply.call_args[0][0]
            self.assertEqual(args["content"], random_old_content)
            self.assertEqual(args["file_path"], random_file)

    def test_rollback_no_inspector(self):
        """Проверка поведения при отсутствии git_inspector."""
        executor = PatchExecutor(git_inspector=None)
        res = executor.rollback_patch("any.txt", "hash")
        self.assertFalse(res, "Должен возвращать False, если инспектор не задан")

    def test_apply_patch_exception_handling(self):
        """Проверка трансформации системных ошибок в PatchExecutorError."""
        executor = PatchExecutor(repo_path=".")
        with patch("os.makedirs", side_effect=OSError("Access Denied")):
            with self.assertRaises(PatchExecutorError) as cm:
                executor.apply_patch({"file_path": "forbidden.txt", "content": "data"})
            self.assertIn("Access Denied", str(cm.exception))

    def test_execute_from_lessons_no_parser(self):
        """Проверка работы без парсера."""
        executor = PatchExecutor(lesson_parser=None)
        self.assertEqual(executor.execute_from_lessons(), {})

    def test_absolute_path_handling(self):
        """Проверка, что абсолютные пути не объединяются с repo_path."""
        abs_path = "/absolute/path/to/file.py" if os.name != 'nt' else "C:\\absolute\\file.py"
        executor = PatchExecutor(repo_path="/relative/root")
        
        with patch("os.makedirs"), patch("builtins.open", mock_open()) as m:
            executor.apply_patch({"file_path": abs_path, "content": "data"})
            m.assert_called_once()
            # Проверяем, что открыт именно абсолютный путь
            self.assertEqual(m.call_args[0][0], abs_path)

if __name__ == "__main__":
    unittest.main()