from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_scheduler import PatchScheduler
from skills.auto_patch_pipeline import PipelineResult

error_recovery_hub = ErrorRecoveryHub()
patch_scheduler = PatchScheduler()


def auto_patch_pipeline(module_name, exception, traceback_str):
    hub = ErrorRecoveryHub()
    scheduler = PatchScheduler()

    history = hub.get_incident_history(module_name) if hasattr(hub, "get_incident_history") else []
    if history and isinstance(history, list) and len(history) > 0 and isinstance(history[0], dict) and "incident_id" in history[0]:
        incident_id = history[0].get("incident_id")
    else:
        incident_id = hub.capture_failure(module_name, exception, traceback_str)

    analysis = hub.analyze_failure(incident_id) if hasattr(hub, "analyze_failure") else {}
    patch_data = hub.generate_patch(incident_id) if hasattr(hub, "generate_patch") else {}

    deploy_res = hub.deploy_and_verify(incident_id, patch_data) if hasattr(hub, "deploy_and_verify") else True
    scheduled_res = scheduler.coordinate_and_schedule(incident_id, {
        "module_name": module_name,
        "patch_data": patch_data,
        "success": bool(deploy_res)
    }, hub) if hasattr(scheduler, "coordinate_and_schedule") else True

    is_scheduled = scheduled_res.success if hasattr(scheduled_res, 'success') else bool(scheduled_res)
    success = bool(deploy_res) and is_scheduled
    error_msg = None if success else str(exception)

    return PipelineResult(
        success=success,
        incident_id=incident_id,
        error=error_msg,
        raw_result=scheduled_res,
        patch_data=patch_data
    )


def execute_auto_patch_pipeline(module_name, exception, traceback_str):
    return auto_patch_pipeline(module_name, exception, traceback_str)


def execute_stream_patch_pipeline(module_name, stream):
    scheduler = PatchScheduler()
    return scheduler.process_stream(module_name, stream)


def batch_auto_patch_runner(failures_list):
    scheduler = PatchScheduler()
    return scheduler.batch_schedule(failures_list)
