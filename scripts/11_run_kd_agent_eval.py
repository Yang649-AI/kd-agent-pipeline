import json

from kd_agent.config import default_config
from kd_agent.evaluation import run_evaluation


def main() -> None:
    metrics = run_evaluation(default_config())
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
