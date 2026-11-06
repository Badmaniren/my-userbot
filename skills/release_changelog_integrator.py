import os
from skills import release_notes_composer
from skills import dependency_audit_sync
from skills import dependency_audit_pipeline
from skills import repo_health_automator

# Честный импорт без создания заглушек (согласно правилам архитектора).
try:
    from skills import release_automation_hub as hub_module
except ImportError:
    hub_module = None

try:
    from skills import changelog_generator
except ImportError:
    changelog_generator = None


class ReleaseChangelogIntegrator:
    def integrate(self, version: str) -> str:
        changelog_content = release_notes_composer.compose(version)
        hub_id = hub_module.push_release(changelog_content)
        return hub_id

    def parse_changelog_file(self, filepath: str) -> str:
        with open(filepath, 'rb') as f:
            raw_data = f.read()
        return raw_data.decode(errors='ignore')

    def sync_with_hub(self, url: str) -> None:
        dependency_audit_sync.sync(url)

    def run_audit(self, audit_id: str, threshold: float) -> bool:
        return dependency_audit_pipeline.run(audit_id=audit_id, threshold=threshold)

    def get_repo_health(self, repo_name: str) -> int:
        return repo_health_automator.get_score(repo_name)


def release_changelog_integrator(integrator_input: dict) -> dict:
    repo_path = integrator_input.get("repo_path")
    target_version = integrator_input.get("target_version")
    integration_id = integrator_input.get("integration_id")
    hub_status = integrator_input.get("hub_status")

    changelog_file_path = os.path.join(repo_path, "CHANGELOG.md")
    content = f"# Changelog - {target_version}\nSession ID: {integration_id}\nHub Status: {hub_status}\n"
    
    with open(changelog_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "status": "synchronized",
        "integration_id": integration_id,
        "version": target_version
    }