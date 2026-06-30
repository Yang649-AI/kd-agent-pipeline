import os
from huggingface_hub import hf_hub_download

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

local_path = hf_hub_download(
    repo_id="Qwen/Qwen3-8B-GGUF",
    filename="Qwen3-8B-Q4_K_M.gguf",
    local_dir="/root/autodl-tmp/kd_agent_pipeline/models/gguf",
    local_dir_use_symlinks=False,
    resume_download=True,
)

print("Downloaded to:", local_path)
