from kd_agent.build import build_index
from kd_agent.config import default_config


def main() -> None:
    stats = build_index(default_config())
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
