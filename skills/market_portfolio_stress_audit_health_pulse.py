import sys
import os

from skills.db_storage import db_storage
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.market_report_generator import market_report_generator


def get_all_subsystems():
    return {
        "db_storage": db_storage(),
        "market_portfolio_stress_scenario_pipeline": market_portfolio_stress_scenario_pipeline(),
        "market_report_generator": market_report_generator()
    }


def start_new():
    subsystems = get_all_subsystems()
    unhealthy = []
    for name, sub in subsystems.items():
        if hasattr(sub, 'health_check'):
            if not sub.health_check():
                unhealthy.append(name)
        else:
            unhealthy.append(name)

    if unhealthy:
        return {"status": "UNHEALTHY", "unhealthy_subsystems": unhealthy}
    return {"status": "HEALTHY"}
