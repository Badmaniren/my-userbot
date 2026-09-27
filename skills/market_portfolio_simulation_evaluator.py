import io
import os
import sys

skills_dir = os.path.dirname(os.path.abspath(__file__))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    import market_portfolio_scenario_simulator
    from market_portfolio_scenario_simulator import PortfolioScenarioSimulator
except ImportError:
    from skills import market_portfolio_scenario_simulator
    from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

try:
    import market_portfolio_performance_analytics
    from market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
except ImportError:
    from skills import market_portfolio_performance_analytics
    from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics

sys.modules.setdefault("market_portfolio_scenario_simulator", market_portfolio_scenario_simulator)
sys.modules.setdefault("market_portfolio_performance_analytics", market_portfolio_performance_analytics)


class PortfolioSimulationEvaluator:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file
        self.simulator = market_portfolio_scenario_simulator.PortfolioScenarioSimulator(storage_file)
        self.analytics = market_portfolio_performance_analytics.PortfolioPerformanceAnalytics(storage_file)

    def evaluate_scenario(self, symbol, percentage):
        try:
            sim_result = self.simulator.simulate_scenario(symbol, percentage)
        except Exception as e:
            return {"error": str(e)}

        perf_result = {}
        if hasattr(self.analytics, "calculate_metrics"):
            try:
                perf_result = self.analytics.calculate_metrics(symbol)
            except TypeError:
                try:
                    perf_result = self.analytics.calculate_metrics()
                except Exception as e:
                    perf_result = {"error": str(e)}
            except Exception as e:
                perf_result = {"error": str(e)}

        if not perf_result and hasattr(self.analytics, "evaluate_performance"):
            try:
                perf_result = self.analytics.evaluate_performance(symbol)
            except TypeError:
                try:
                    perf_result = self.analytics.evaluate_performance()
                except Exception as e:
                    perf_result = {"error": str(e)}
            except Exception as e:
                perf_result = {"error": str(e)}

        if isinstance(sim_result, dict) and isinstance(perf_result, dict):
            return {**sim_result, **perf_result, "simulation": sim_result, "analytics": perf_result}
        return {
            "simulation": sim_result,
            "analytics": perf_result
        }

    def simulate_and_evaluate(self, symbol, percentage):
        return self.evaluate_scenario(symbol, percentage)

    def evaluate_stress_test(self, symbol, shifts):
        try:
            sim_result = self.simulator.run_stress_test(symbol, shifts)
        except Exception as e:
            return {"error": str(e)}

        perf_result = {}
        if hasattr(self.analytics, "evaluate_performance"):
            try:
                perf_result = self.analytics.evaluate_performance(symbol)
            except TypeError:
                try:
                    perf_result = self.analytics.evaluate_performance()
                except Exception as e:
                    perf_result = {"error": str(e)}
            except Exception as e:
                perf_result = {"error": str(e)}

        if not perf_result and hasattr(self.analytics, "calculate_metrics"):
            try:
                perf_result = self.analytics.calculate_metrics(symbol)
            except TypeError:
                try:
                    perf_result = self.analytics.calculate_metrics()
                except Exception as e:
                    perf_result = {"error": str(e)}
            except Exception as e:
                perf_result = {"error": str(e)}

        if isinstance(sim_result, dict) and isinstance(perf_result, dict):
            return {**sim_result, **perf_result, "simulation": sim_result, "analytics": perf_result}
        return {
            "simulation": sim_result,
            "analytics": perf_result
        }

    def run_stress_evaluation(self, symbol, shifts):
        return self.evaluate_stress_test(symbol, shifts)

    def load_data(self, target_file):
        with open(target_file, "rb") as f:
            f.read()


MarketPortfolioSimulationEvaluator = PortfolioSimulationEvaluator


def evaluate_portfolio_simulation(storage_file, symbol, percentage):
    evaluator = PortfolioSimulationEvaluator(storage_file=storage_file)
    return evaluator.evaluate_scenario(symbol, percentage)


def evaluate_market_scenario(storage_file, symbol, percentage):
    return evaluate_portfolio_simulation(storage_file, symbol, percentage)
