import os
import subprocess
import base64
import requests


class GitCommitter:
    def __init__(self, repo_path: str = ".", github_token: str = None):
        self.repo_path = repo_path
        self.github_token = github_token

    def commit_and_push_local(self, files: list, message: str, branch: str = "main") -> bool:
        try:
            # 1. Checkout / create branch
            subprocess.run(["git", "-C", self.repo_path, "checkout", "-B", branch], check=True, capture_output=True)

            # 2. Add files
            subprocess.run(["git", "-C", self.repo_path, "add"] + files, check=True, capture_output=True)

            # 3. Check status to see if there are changes
            res_status = subprocess.run(["git", "-C", self.repo_path, "status", "--porcelain"], check=True, capture_output=True)
            if not res_status.stdout.strip():
                return False

            # 4. Commit
            subprocess.run(["git", "-C", self.repo_path, "commit", "-m", message], check=True, capture_output=True)

            # 5. Push
            subprocess.run(["git", "-C", self.repo_path, "push", "origin", branch], check=True, capture_output=True)

            return True
        except Exception:
            return False

    def commit_changes(self, file_paths: list, message: str) -> str:
        subprocess.run(["git", "-C", self.repo_path, "add"] + file_paths, check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", message], check=True, capture_output=True)
        res = subprocess.run(
            ["git", "-C", self.repo_path, "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True
        )
        return res.stdout.strip()

    def push_via_github_api(self, owner: str, repo: str, file_path: str, content: str, message: str, branch: str = "main"):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json"
        }
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {
            "message": message,
            "content": encoded_content,
            "branch": branch
        }
        try:
            response = requests.put(url, json=payload, headers=headers)
            if response.status_code in (200, 201):
                data = response.json()
                return data.get("content", {}).get("sha")
            return None
        except Exception:
            return None
