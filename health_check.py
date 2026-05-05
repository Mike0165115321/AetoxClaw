import os
import sys
import logging
from pathlib import Path

# Setup simple logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("aetox.health_check")

def check_structure():
    required_dirs = ["aetox", "config", "data", "tests"]
    for d in required_dirs:
        if os.path.isdir(d):
            logger.info(f"✅ Directory found: {d}")
        else:
            logger.error(f"❌ Missing directory: {d}")

def check_configs():
    configs = ["config/models.yaml", "config/permissions.yaml"]
    for c in configs:
        if os.path.isfile(c):
            logger.info(f"✅ Config file found: {c}")
        else:
            logger.warning(f"⚠️ Missing config: {c} (System may use defaults)")

def check_imports():
    try:
        from aetox.core.config_loader import config_loader
        from aetox.tools.loader import create_default_registry
        from aetox.agents.executor import ExecutorAgent
        logger.info("✅ Core components imported successfully.")
        
        registry = create_default_registry()
        logger.info(f"✅ Tool Registry initialized with {len(registry.list_names())} tools.")
        
    except Exception as e:
        logger.error(f"❌ Import/Initialization failed: {e}")

def check_environment():
    if os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL"):
        logger.info(f"✅ Ollama environment set.")
    else:
        logger.warning("⚠️ OLLAMA_HOST not set. Using default http://localhost:11434")

if __name__ == "__main__":
    logger.info("=== AetoxClaw Health Check ===")
    check_structure()
    check_configs()
    check_environment()
    check_imports()
    logger.info("=== Health Check Finished ===")
