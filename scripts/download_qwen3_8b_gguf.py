import os
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common.paths import PROJECT_ROOT

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"


def main():
    local_path = hf_hub_download(
        repo_id="Qwen/Qwen3-8B-GGUF",
        filename="Qwen3-8B-Q4_K_M.gguf",
        local_dir=str(PROJECT_ROOT / "models" / "gguf"),
        local_dir_use_symlinks=False,
        resume_download=True,
    )

    print("Downloaded to:", local_path)


if __name__ == "__main__":
    main()
