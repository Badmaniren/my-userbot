from skills.patch_scheduler import PatchScheduler
from skills.auto_patch_pipeline import AutoPatchPipeline
import io

class PatchAutoExecutor:
    def __init__(self):
        self.scheduler = PatchScheduler()
        self.pipeline = AutoPatchPipeline()

    def execute_auto_patch(self, module_name, exception, traceback_str, context=None):
        try:
            scheduled = self.scheduler.schedule_patch(module_name, exception, traceback_str)
        except TypeError:
            scheduled = self.scheduler.schedule_patch(module_name, exception, traceback_str, context)

        if scheduled:
            return self.pipeline.run_pipeline(module_name, exception, traceback_str, context)
        return None

    def execute_stream_patch(self, module_name, stream):
        if isinstance(stream, str):
            stream = io.BytesIO(stream.encode('utf-8'))
        elif not hasattr(stream, 'read'):
            stream = io.BytesIO(str(stream).encode('utf-8'))

        try:
            processed = self.scheduler.process_stream(module_name, stream)
        except Exception:
            stream.seek(0)
            processed = stream

        if hasattr(processed, "raw_result") and processed.raw_result:
            stream_to_verify = io.BytesIO(processed.raw_result.encode('utf-8') if isinstance(processed.raw_result, str) else processed.raw_result)
        elif hasattr(processed, "patch_data") and processed.patch_data:
            data = processed.patch_data
            if isinstance(data, str):
                stream_to_verify = io.BytesIO(data.encode('utf-8'))
            else:
                stream_to_verify = processed
        elif hasattr(processed, 'read'):
            stream_to_verify = processed
        else:
            stream_to_verify = io.BytesIO(str(processed).encode('utf-8'))

        return self.pipeline.verify_patch_stream(stream_to_verify)

    def execute_auto_patch_workflow(self, module_name, exception, traceback_str, context):
        return self.execute_auto_patch(module_name, exception, traceback_str, context)

    def process_and_verify_stream(self, module_name, stream):
        return self.execute_stream_patch(module_name, stream)