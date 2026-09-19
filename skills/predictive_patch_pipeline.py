from skills.predictive_vulnerability_telemetry_bridge import PredictiveVulnerabilityTelemetryBridge
from skills.preventive_patch_applier import PreventivePatchApplier


class PredictivePatchPipelineError(Exception):
    """Custom exception for PredictivePatchPipeline errors."""
    pass


class PredictivePatchPipeline:
    def __init__(self, bridge=None, applier=None):
        self.bridge = bridge if bridge is not None else PredictiveVulnerabilityTelemetryBridge()
        self.applier = applier if applier is not None else PreventivePatchApplier()

    def run_comprehensive_predictive_patch_cycle(self, *args, **kwargs):
        if args:
            module_name = args[0]
        else:
            module_name = kwargs.get("module_name")

        telemetry_res = self.bridge.run_vulnerability_telemetry_cycle(*args, **kwargs)
        patch_res = self.applier.run_preventive_cycle(module_name)
        return {
            "telemetry_cycle": telemetry_res,
            "preventive_cycle": patch_res,
            "module_name": module_name
        }

    def process_stream_and_apply_patches(self, module_name, stream_io, path):
        stream_result = self.bridge.process_stream_and_telemetry(stream_io, path)
        prevent_result = self.applier.prevent_failures_from_stream(module_name, stream_io)
        return {
            "stream_processing": stream_result,
            "preventive_stream_result": prevent_result,
            "module_name": module_name
        }

    def execute_full_pipeline_flow(self, **kwargs):
        module_name = kwargs.get("module_name")
        bridge_output = self.bridge.execute_bridge_pipeline(**kwargs)
        apply_output = self.applier.apply_preventive_patches(module_name)
        return {
            "bridge_pipeline": bridge_output,
            "apply_preventive_patches": apply_output,
            "module_name": module_name
        }

    def export_and_apply_pipeline(self, payload, path, module_name):
        self.bridge.export_risk_and_vulnerability_report(payload, path)
        process_output = self.applier.process_module(module_name)
        return {
            "process_module": process_output,
            "report_exported": True,
            "module_name": module_name
        }

    def run(self, *args, **kwargs):
        return self.run_comprehensive_predictive_patch_cycle(*args, **kwargs)

    def execute(self, *args, **kwargs):
        return self.run_comprehensive_predictive_patch_cycle(*args, **kwargs)

    def run_pipeline(self, *args, **kwargs):
        return self.run_comprehensive_predictive_patch_cycle(*args, **kwargs)

    def execute_pipeline(self, *args, **kwargs):
        return self.run_comprehensive_predictive_patch_cycle(*args, **kwargs)

    def run_cycle(self, *args, **kwargs):
        return self.run_comprehensive_predictive_patch_cycle(*args, **kwargs)

    def process(self, *args, **kwargs):
        return self.run_comprehensive_predictive_patch_cycle(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.run_comprehensive_predictive_patch_cycle(*args, **kwargs)