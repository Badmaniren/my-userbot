import os
from skills.changelog_generator import ChangelogGenerator
from skills.repo_auditor import RepoAuditor

class ReleaseNotesComposer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.changelog_generator = ChangelogGenerator(repo_path)
        self.repo_auditor = RepoAuditor(repo_path)

    def compose(self, output_path: str) -> str:
        self.changelog_generator.generate(output_path)
        changelog_text = self.changelog_generator.get_changelog()
        
        audit_report_path = self.repo_auditor.generate_report(os.path.join(os.path.dirname(output_path), "audit.json"))
        metrics = self.repo_auditor.calculate_metrics()

        content = f"# Release Notes\n\n## Changelog\n{changelog_text}\n\n## Audit Metrics\n- Score: {metrics.get('score', 'N/A')}\n- Report: {audit_report_path}\n"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return content

    def generate(self, output_path: str) -> str:
        return self.compose(output_path)

    def run(self) -> str:
        default_output = os.path.join(self.repo_path, "release.md")
        return self.compose(default_output)