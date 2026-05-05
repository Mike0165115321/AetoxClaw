import importlib
import logging
from pathlib import Path
from aetox.tools.registry import ToolRegistry
from aetox.tools.base import BaseTool

logger = logging.getLogger("aetox.tools.loader")

def load_tools(registry: ToolRegistry, tools_dir: str = "aetox/tools") -> None:
    """
    Auto-scan โฟลเดอร์ tools/ แล้ว register ทุก Tool ที่เจอ
    กฎ: ไฟล์ต้องมี class ที่ inherit BaseTool
    ข้าม: __init__.py, base.py, registry.py, loader.py, โฟลเดอร์ doc/
    """
    skip_files = {"__init__", "base", "registry", "loader"}
    tools_path = Path(tools_dir)

    for py_file in sorted(tools_path.glob("*.py")):
        module_name = py_file.stem

        if module_name in skip_files:
            continue

        try:
            # Dynamic import
            full_module = f"aetox.tools.{module_name}"
            module = importlib.import_module(full_module)

            # หา class ที่ inherit BaseTool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseTool)
                    and attr is not BaseTool
                ):
                    # Inject registry for SystemControl to enable capability listing
                    if attr.__name__ == "SystemControl":
                        instance = attr(registry=registry)
                    else:
                        instance = attr()
                    registry.register(instance)
                    break

        except Exception as e:
            logger.error(f"❌ โหลด tool ล้มเหลว ({module_name}): {e}")

def create_default_registry() -> ToolRegistry:
    """
    Shortcut: สร้าง registry พร้อม load tools ทั้งหมดในครั้งเดียว
    ใช้ใน executor แทน hardcode list
    """
    registry = ToolRegistry()
    load_tools(registry)
    return registry
