from kd_agent.config import default_config
from kd_agent.reporting import generate_report


def main() -> None:
    config = default_config()
    generate_report(config)
    print(f"Report saved to: {config.report_path}")


if __name__ == "__main__":
    main()
