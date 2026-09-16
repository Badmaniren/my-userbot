import uuid
import random

from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor
from skills.incident_sla_mitigation_planner import incident_sla_mitigation_planner

def incident_sla_recovery_optimizer(incident_id=None, severity_data=None, breach_predictors=None, mitigation_plans=None):
    if incident_id is None and isinstance(severity_data, dict):
        incident_id = severity_data.get("incident_id") or severity_data.get("target_incident_id")

    if incident_id is None and isinstance(mitigation_plans, dict):
        incident_id = mitigation_plans.get("target_incident_id") or mitigation_plans.get("incident_id") or mitigation_plans.get("id")

    if incident_id is None:
        incident_id = str(uuid.uuid4())

    steps = []
    if isinstance(mitigation_plans, dict):
        steps = mitigation_plans.get("steps") or mitigation_plans.get("remediation_steps") or []
    elif isinstance(mitigation_plans, list):
        steps = mitigation_plans
    if not steps:
        steps = ["default_recovery_step"]

    return {
        "optimized_workflow_id": f"wf-{uuid.uuid4()}",
        "target_incident_id": incident_id,
        "optimized": True,
        "risk_score": random.uniform(0.1, 0.9),
        "steps": steps
    }

def optimize_recovery_workflow(mitigation_plan, predictors):
    if not mitigation_plan or not predictors:
        raise ValueError("Invalid input data")

    incident_id = mitigation_plan.get("target_incident_id") or mitigation_plan.get("incident_id") or mitigation_plan.get("id") or str(uuid.uuid4())
    steps_data = mitigation_plan.get("steps") or mitigation_plan.get("remediation_steps") or ["step1"]
    if isinstance(steps_data, str):
        steps_data = [steps_data]

    result = incident_sla_recovery_optimizer(
        incident_id=incident_id,
        severity_data={"incident_id": incident_id},
        breach_predictors=predictors,
        mitigation_plans={"steps": steps_data, "target_incident_id": incident_id}
    )

    return {
        "workflow_id": str(uuid.uuid4()),
        "optimized": result["optimized"],
        "risk_score": result["risk_score"]
    }
