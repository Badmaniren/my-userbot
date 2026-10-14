import json
from skills.git_inspector import GitInspector


class LessonParser:
    def __init__(self, repo_path=None, inspector=None):
        self.repo_path = repo_path
        self._inspector = inspector

    @property
    def inspector(self):
        if self._inspector is None:
            self._inspector = GitInspector(self.repo_path)
        return self._inspector

    @inspector.setter
    def inspector(self, value):
        self._inspector = value

    def parse_lesson_history(self, file_path):
        commits = self.inspector.get_commit_history()
        target_commit = None
        for commit in commits:
            msg = commit.get("message", "")
            if "Fixed" in msg:
                target_commit = commit.get("commit") or commit.get("hash")
                break
        if not target_commit and commits:
            target_commit = commits[0].get("commit") or commits[0].get("hash")

        if target_commit:
            raw_content = self.inspector.read_file_at_commit(target_commit, file_path)
        else:
            raw_content = ""

        if isinstance(raw_content, bytes):
            text_content = raw_content.decode("utf-8")
        else:
            text_content = str(raw_content)

        parsed_items = []
        for line in text_content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                parsed_items.append(item)
            except json.JSONDecodeError:
                parsed_items.append({"raw_line": line})

        return parsed_items

    def extract_error_patterns(self):
        latest_changes = self.inspector.get_latest_changes()
        diffs = []
        if latest_changes:
            if isinstance(latest_changes, list):
                for change in latest_changes:
                    if isinstance(change, dict):
                        commit_hash = change.get("hash") or change.get("commit")
                        if commit_hash:
                            diff = self.inspector.get_file_diff(commit_hash)
                            if diff:
                                diffs.append(diff)
            elif isinstance(latest_changes, str):
                diffs.append(latest_changes)

        if not diffs:
            commits = self.inspector.get_commit_history()
            if commits:
                for commit in commits:
                    commit_hash = commit.get("hash") or commit.get("commit")
                    if commit_hash:
                        diff = self.inspector.get_file_diff(commit_hash)
                        if diff:
                            diffs.append(diff)
                            break

        combined_diffs = "\n".join([str(d) for d in diffs if d is not None])

        return {
            "patterns": {
                "diff_content": combined_diffs
            }
        }

    def prepare_hypothesis_data(self):
        analysis = self.inspector.analyze_repository()
        hypotheses_inputs = []
        if isinstance(analysis, dict):
            for name, data in analysis.items():
                if isinstance(data, dict):
                    item = {"name": name}
                    item.update(data)
                    hypotheses_inputs.append(item)
                else:
                    hypotheses_inputs.append({"name": name, "value": data})
        return {
            "hypotheses_inputs": hypotheses_inputs
        }
