from skills.repo_auditor import RepoAuditor
from skills.repo_tagger import RepoTagger


class RepoCIPipeline:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.auditor = RepoAuditor(repo_path)
        self.tagger = RepoTagger(repo_path)

    def run_pipeline(self) -> bool:
        audit_success = self.auditor.audit()
        if not audit_success:
            self.auditor.detect_issues()
            return False

        issues = self.auditor.detect_issues()
        if issues:
            return False

        self.auditor.calculate_metrics()

        if not self.tagger.evaluate_release_readiness():
            return False

        next_version = self.tagger.determine_next_version()
        if not next_version:
            return False

        applied = self.tagger.apply_and_push_tag(next_version)
        if not applied:
            return False

        return True

    def run(self) -> bool:
        return self.run_pipeline()

    def execute(self) -> bool:
        return self.run_pipeline()

    def process_audit_stream(self, stream):
        return self.auditor.process_stream(stream)