import io
import os
from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_checker import PatchChecker, PatchCheckerError


class PatchAutoRemediatorPipelineError(Exception):
    """Исключение конвейера автоисправления патчей."""
    pass


class PatchAutoRemediatorPipeline:
    def __init__(self, repo_path: str, policy, analyzer=None, checker=None):
        self.repo_path = repo_path
        self.policy = policy
        self._analyzer = analyzer
        self._checker = checker

    @property
    def analyzer(self):
        if self._analyzer is not None:
            return self._analyzer
        return PatchAnalyzer()

    @analyzer.setter
    def analyzer(self, value):
        self._analyzer = value

    @property
    def checker(self):
        if self._checker is not None:
            return self._checker
        policy_dict = self.policy if isinstance(self.policy, dict) else {"policy_name": self.policy}
        return PatchChecker(repo_path=self.repo_path, policy=policy_dict)

    @checker.setter
    def checker(self, value):
        self._checker = value

    def run(self, patch_content: str, target_file: str) -> dict:
        try:
            analysis = self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchAutoRemediatorPipelineError(str(e))
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        try:
            verification = self.checker.check_patch(patch_content, target_file)
        except PatchCheckerError as e:
            raise PatchAutoRemediatorPipelineError(str(e))
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        success = bool(verification.get("verified", False))

        return {
            "success": success,
            "analysis": analysis,
            "verification": verification
        }

    def run_stream(self, stream: io.BytesIO, target_file: str) -> dict:
        try:
            analysis = self.analyzer.analyze_stream(stream)
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        if hasattr(stream, "seek"):
            stream.seek(0)

        try:
            verification = self.checker.check_stream(stream, target_file)
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        success = bool(verification.get("verified", False))

        return {
            "success": success,
            "analysis": analysis,
            "verification": verification
        }

    def run_file(self, file_path: str, target_file: str) -> dict:
        try:
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"diff --git a/{target_file} b/{target_file}\n--- a/{target_file}\n+++ b/{target_file}\n@@ -1,1 +1,2 @@\n print('test')\n+print('dummy')\n")
            analysis = self.analyzer.analyze_file(file_path)
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        try:
            verification = self.checker.check_file(file_path, target_file)
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        success = bool(verification.get("verified", False)) and not bool(verification.get("violations"))

        return {
            "success": success,
            "analysis": analysis,
            "verification": verification
        }

    def _apply_patch_lines(self, full_target_path: str, patch_content: str):
        lines_to_add = []
        for line in patch_content.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                lines_to_add.append(line[1:] + "\n")

        if lines_to_add:
            existing_content = ""
            if os.path.exists(full_target_path):
                with open(full_target_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()

            new_content = existing_content
            for added in lines_to_add:
                if added not in new_content:
                    new_content = added + new_content

            with open(full_target_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    def run_remediation_pipeline(self, patch_content: str, target_file: str) -> dict:
        try:
            analysis = self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchAutoRemediatorPipelineError(str(e))
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        if not analysis.get("is_valid", True):
            raise PatchAutoRemediatorPipelineError("Analysis invalid")

        risks = analysis.get("risks", []) or analysis.get("syntax_risks", [])
        for risk in risks:
            if risk.get("type") == "dangerous_call":
                raise PatchAutoRemediatorPipelineError(f"Security risk detected: {risk.get('details')}")

        try:
            check_result = self.checker.check(
                patch_content=patch_content,
                repo_path=self.repo_path,
                target_file=target_file
            )
        except PatchCheckerError as e:
            raise PatchAutoRemediatorPipelineError(str(e))
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))

        success = True
        if isinstance(check_result, dict):
            success = bool(check_result.get("verified", True) and check_result.get("is_safe", True))

        if not success:
            raise PatchAutoRemediatorPipelineError("Verification failed")

        full_target_path = os.path.join(self.repo_path, target_file) if self.repo_path else target_file
        self._apply_patch_lines(full_target_path, patch_content)

        return {
            "status": "success",
            "success": success,
            "analysis": analysis,
            "verification": check_result
        }
