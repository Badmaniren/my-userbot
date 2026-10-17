import io
import os
from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_checker import PatchChecker, PatchCheckerError


class PatchAutoRemediatorPipelineError(Exception):
    """Исключение конвейера автоисправления патчей."""
    pass


class PatchAutoRemediatorPipeline:
    def __init__(self, repo_path: str, policy):
        self.repo_path = repo_path
        self.policy = policy
        self.analyzer = PatchAnalyzer()
        self.checker = PatchChecker()

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
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("")
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

    def run_remediation_pipeline(self, patch_content: str, target_file: str) -> dict:
        try:
            analysis = self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchAutoRemediatorPipelineError(str(e))
        except Exception as e:
            raise PatchAutoRemediatorPipelineError(str(e))
        
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
            success = bool(check_result.get("verified", True))

        return {
            "status": "success",
            "success": success,
            "analysis": analysis,
            "verification": check_result
        }