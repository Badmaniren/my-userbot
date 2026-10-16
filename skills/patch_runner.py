from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError
from skills.patch_executor import PatchExecutor, PatchExecutorError

class PatchRunnerError(Exception):
    pass

class PatchRunner:
    def __init__(self, repo_path, sanitizer=None, validator=None, git_inspector=None, lesson_parser=None, autocorrector=None, executor=None):
        self.repo_path = repo_path
        self.sanitizer = sanitizer
        self.validator = validator
        self.git_inspector = git_inspector
        self.lesson_parser = lesson_parser

        if autocorrector is not None:
            self.autocorrector = autocorrector
        else:
            self.autocorrector = PatchAutocorrector(
                repo_path=repo_path,
                sanitizer=sanitizer,
                validator=validator
            )

        if executor is not None:
            self.executor = executor
        else:
            self.executor = PatchExecutor(
                repo_path=repo_path,
                git_inspector=git_inspector,
                lesson_parser=lesson_parser
            )

    def run_patch(self, patch_data):
        try:
            code_key = "code" if "code" in patch_data else "content"
            raw_code = patch_data.get(code_key, "")

            corrected_code = self.autocorrector.correct_and_validate(raw_code)

            execution_payload = dict(patch_data)
            execution_payload[code_key] = corrected_code
            if "code" in execution_payload and "content" not in execution_payload:
                execution_payload["content"] = corrected_code
            elif "content" in execution_payload and "code" not in execution_payload:
                execution_payload["code"] = corrected_code

            return self.executor.apply_patch(execution_payload)
        except PatchAutocorrectorError as e:
            raise PatchRunnerError(str(e))
        except PatchExecutorError as e:
            raise PatchRunnerError(str(e))

    def execute_pipeline_from_lessons(self):
        return self.executor.execute_from_lessons()

    def rollback_operation(self, file_path, commit_hash):
        return self.executor.rollback_patch(file_path, commit_hash)

    def process_stream(self, stream):
        if isinstance(stream, str):
            import io
            stream = io.StringIO(stream)
        try:
            return self.autocorrector.transform_stream(stream)
        except Exception as e:
            raise PatchRunnerError(str(e)) from e