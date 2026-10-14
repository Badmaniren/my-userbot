import unittest
import tempfile
import shutil
import os
import subprocess
import uuid
import random
from skills.git_inspector import GitInspector

class TestGitInspectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        subprocess.run(['git', '-C', self.repo_path, 'init', '-b', 'main'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(['git', '-C', self.repo_path, 'config', 'user.name', 'ArchitectTest'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(['git', '-C', self.repo_path, 'config', 'user.email', 'architect@test.com'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_repository_inspection_integration(self):
        inspector = GitInspector(self.repo_path)
        
        initial_analysis = inspector.analyze_repository()
        self.assertEqual(initial_analysis['total_commits'], 0)
        self.assertEqual(initial_analysis['total_files'], 0)
        self.assertEqual(initial_analysis['repo_path'], self.repo_path)

        file_name = f"lesson_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.repo_path, file_name)
        
        unique_content = f"print('Hello {uuid.uuid4()}')\n"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(unique_content)

        subprocess.run(['git', '-C', self.repo_path, 'add', file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        commit_message = f"Add lesson {uuid.uuid4().hex[:6]}"
        subprocess.run(['git', '-C', self.repo_path, 'commit', '-m', commit_message], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        history = inspector.get_commit_history(max_count=10)
        self.assertEqual(len(history), 1)
        
        commit_hash = history[0]['hash']
        self.assertEqual(history[0]['message'], commit_message)
        self.assertTrue(len(commit_hash) >= 7)

        file_content_at_commit = inspector.read_file_at_commit(commit_hash, file_name)
        self.assertEqual(file_content_at_commit, unique_content)

        diff = inspector.get_file_diff(commit_hash)
        self.assertIn(file_name, diff)
        self.assertIn("print('Hello", diff)

        latest_changes = inspector.get_latest_changes()
        self.assertIn(commit_message, latest_changes)

        analysis = inspector.analyze_repository()
        self.assertEqual(analysis['total_commits'], 1)
        self.assertEqual(analysis['total_files'], 1)

        second_file_name = f"exercise_{uuid.uuid4().hex[:8]}.txt"
        second_file_path = os.path.join(self.repo_path, second_file_name)
        second_content = f"Data {random.randint(1000, 9999)}"
        with open(second_file_path, 'w', encoding='utf-8') as f:
            f.write(second_content)

        subprocess.run(['git', '-C', self.repo_path, 'add', second_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        second_commit_msg = f"Update repo {uuid.uuid4().hex[:6]}"
        subprocess.run(['git', '-C', self.repo_path, 'commit', '-m', second_commit_msg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        full_history = inspector.get_history()
        self.assertEqual(len(full_history), 2)
        self.assertEqual(full_history[0]['message'], second_commit_msg)
        self.assertEqual(full_history[1]['message'], commit_message)

if __name__ == '__main__':
    unittest.main()