import os
from pathlib import Path


def get_project_root() -> Path:
    env_root = os.getenv("KD_AGENT_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "requirements-baseline.txt").is_file() and (candidate / "configs").is_dir():
            return candidate

    return Path.cwd().resolve()


PROJECT_ROOT = get_project_root()
