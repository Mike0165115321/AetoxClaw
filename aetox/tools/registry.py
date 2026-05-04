import logging
from typing import Dict, Optional
from aetox.tools.base import BaseTool

logger = logging.getLogger("aetox.tools.registry")

class ToolRegistry:
    """
    ศูนย์กลางลงทะเบียน Tool ทั้งหมด
    - executor ถามแค่ registry ไม่รู้จัก tool โดยตรง
    - เพิ่ม tool = register() แค่จุดเดียว
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """ลงทะเบียน tool เข้า registry"""
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' ถูก override แล้ว")
        self._tools[tool.name] = tool
        logger.info(f"✅ Tool registered: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """ดึง tool ตามชื่อ คืน None ถ้าไม่เจอ"""
        return self._tools.get(name)

    def get_all(self) -> Dict[str, BaseTool]:
        """คืน tool ทั้งหมด"""
        return dict(self._tools)

    def build_prompt_doc(self) -> str:
        """
        รวม get_prompt_doc() จากทุก tool
        ใช้ inject เข้า executor.yaml {tools} placeholder
        """
        if not self._tools:
            return "ไม่มีเครื่องมือที่พร้อมใช้งาน"

        doc_parts = []
        for i, (name, tool) in enumerate(self._tools.items(), 1):
            doc_parts.append(f"{i}. {tool.get_prompt_doc()}")

        return "\n".join(doc_parts)

    def list_names(self) -> list:
        """คืนชื่อ tool ทั้งหมด"""
        return list(self._tools.keys())

    def execute(self, tool_name: str, params: dict) -> dict:
        """
        Dynamic lookup + execute ในที่เดียว
        executor เรียกแค่นี้ ไม่ต้อง if/elif อีกต่อไป
        """
        tool = self.get(tool_name)
        if not tool:
            return {
                "status": "failure",
                "error": f"ไม่พบเครื่องมือชื่อ '{tool_name}' ในระบบ",
                "available_tools": self.list_names()
            }
        return tool.execute(params)
