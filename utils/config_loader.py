import os
import sys
import yaml
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger("config_loader")

def load_config(config_path: str = "config.yaml") -> dict:
    """Loads configuration from yaml and validates the kill switch."""
    load_dotenv()
    
    # Ensure GitHub token is present
    if not os.getenv("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN is missing in the environment or .env file.")
        sys.exit(1)

    if not os.path.exists(config_path):
        logger.error(f"Configuration file {config_path} not found.")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to parse {config_path}: {e}")
        sys.exit(1)

    if config.get("kill_switch", False):
        logger.warning("Kill switch is active. Exiting immediately.")
        sys.exit(0)

    return config

def get_github_token() -> str:
    """Returns the GitHub token from environment variables."""
    return os.getenv("GITHUB_TOKEN", "")

def get_hf_token() -> str:
    """Returns the HuggingFace API token, if any."""
    return os.getenv("HUGGINGFACE_API_TOKEN", "")
