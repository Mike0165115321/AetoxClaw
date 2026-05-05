import os
import sys
import logging
import httpx
from pathlib import Path

# Fix Windows terminal encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

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

def check_ollama():
    from aetox.core.config_loader import config_loader
    host = os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
    
    if not os.getenv("OLLAMA_HOST") and not os.getenv("OLLAMA_BASE_URL"):
        logger.warning(f"⚠️ OLLAMA_HOST not set. Trying default: {host}")
    else:
        logger.info(f"✅ Ollama environment set: {host}")

    try:
        # Check if Ollama is actually online
        r = httpx.get(f"{host}/api/tags", timeout=3)
        if r.status_code == 200:
            logger.info("✅ Ollama is online")
        else:
            logger.warning(f"⚠️ Ollama returned status {r.status_code}")
    except Exception:
        logger.warning("⚠️ Ollama is OFFLINE — AI features will not work")

def check_imports():
    try:
        from aetox.core.config_loader import config_loader
        from aetox.tools.loader import create_default_registry
        from aetox.agents.executor import ExecutorAgent
        logger.info("✅ Core components imported successfully.")
        
        registry = create_default_registry()
        logger.info(f"✅ Tool Registry initialized with {len(registry.list_names())} tools.")
        for tool in registry.list_names():
            logger.info(f"✅ Tool registered: {tool}")
        
    except Exception as e:
        logger.error(f"❌ Import/Initialization failed: {e}")

if __name__ == "__main__":
    logger.info("=== AetoxClaw Health Check ===")
    check_structure()
    check_configs()
    check_ollama()
    check_imports()
    logger.info("=== Health Check Finished ===")
