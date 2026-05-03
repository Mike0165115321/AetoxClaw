import logging
import os
from typing import Dict, List, Any, Optional
from aetox.core.ollama_client import OllamaClient
from aetox.core.prompt_engine import PromptEngine
from aetox.safety.permission import PermissionManager
from aetox.tools.file_manager import MasterFileManager
from aetox.tools.vision import AetoxVision

logger = logging.getLogger("aetox.agents.executor")

class ExecutorAgent:
    """
    Executor Agent - Master Edition.
    Equipped with MasterFileManager and AetoxVision.
    """
    def __init__(self):
        self.client = OllamaClient()
        self.engine = PromptEngine()
        self.permission_manager = PermissionManager()
        self.file_manager = MasterFileManager()
        self.vision = AetoxVision()
        self.last_path = None # Working memory for paths

    def extract_action(self, task_step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uses LLM to extract intent and parameters accurately with memory context.
        """
        description = task_step.get("description", "")
        
        # System prompt for extraction with explicit examples and MEMORY
        extraction_prompt = (
            "คุณคือผู้ช่วยสกัดคำสั่ง (Intent Extractor) สำหรับ AetoxOS\n"
            "เครื่องมือที่มี:\n"
            "1. master_file_manager: สำหรับจัดระเบียบไฟล์ (organize)\n"
            "2. aetox_vision: สำหรับอ่านเนื้อหาไฟล์หรือดูรายการไฟล์ในโฟลเดอร์ (read)\n"
            "3. chat: สำหรับการสนทนาทั่วไป\n\n"
            f"ความจำล่าสุด: โฟลเดอร์ปัจจุบันที่คุยกันอยู่คือ '{self.last_path or 'ยังไม่มี'}'\n"
            "กฎเหล็ก:\n"
            "- ถ้าผู้ใช้บอกแค่ชื่อไฟล์ ให้รวมเข้ากับ 'ความจำล่าสุด' เพื่อสร้างพาธเต็ม\n"
            "- แยกพาธไฟล์ (Path) ออกจากคำสั่งภาษาไทยให้ชัดเจน\n"
            "โปรดตอบกลับเป็น JSON เท่านั้น:\n"
            "{\n"
            "  \"tool\": \"ชื่อเครื่องมือ\",\n"
            "  \"action\": \"ชื่อคำสั่ง\",\n"
            "  \"params\": {\"path\": \"ที่อยู่ไฟล์/โฟลเดอร์\", \"message\": \"ข้อความแชท\"},\n"
            "  \"confidence\": 0.0-1.0\n"
            "}\n\n"
            f"คำสั่งผู้ใช้: \"{description}\""
        )
        
        try:
            result = self.client.chat(model="qwen2.5:14b", messages=[{"role": "user", "content": extraction_prompt}], format="json")
            content = result.get("message", {}).get("content", "{}")
            import json
            extraction = json.loads(content)
            
            # Smart defaults if extraction is weak
            if extraction.get("confidence", 0) < 0.5:
                return {"tool": "chat", "action": "reply", "params": {"message": description}, "confidence": 1.0}
                
            return extraction
        except Exception as e:
            logger.error(f"Extraction failed, falling back to chat: {e}")
            return {"tool": "chat", "action": "reply", "params": {"message": description}, "confidence": 1.0}

    def run_action(self, extraction: Dict[str, Any], memory_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes tools based on extraction.
        """
        tool = extraction.get("tool")
        action = extraction.get("action")
        params = extraction.get("params", {})
        
        # Save last path if it's a valid directory or file
        if params.get("path") and params.get("path") != ".":
            self.last_path = params.get("path")

        if tool == "master_file_manager":
            return self.file_manager.execute(params)
        
        if tool == "aetox_vision":
            return self.vision.execute(params)

        if tool == "chat":
            # Real AI Chat response with strong persona
            system_prompt = (
                "คุณคือ AetoxOS ระบบปฏิบัติการอัจฉริยะที่พัฒนาโดยทีม Aetox "
                "คุณมีบุคลิกที่เป็นมิตร มืออาชีพ และพร้อมช่วยเหลือผู้ใช้เสมอ "
                "คุณคือ AetoxOS เท่านั้น! ตอบกลับเป็นภาษาไทยเท่านั้นที่สุภาพและเป็นธรรมชาติ"
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extraction.get('params', {}).get('message', '')}
            ]
            
            result = self.client.chat(model="qwen2.5:14b", messages=messages)
            response = result.get("message", {}).get("content", "ขออภัยครับ ผมนึกไม่ออก")
            
            return {
                "status": "success",
                "output": response,
                "memory_updates": {}
            }
            
        return {
            "status": "failure", 
            "error": "ขออภัยครับ ตอนนี้ผมยังไม่มีเครื่องมือสำหรับทำสิ่งนี้ (โหมดพื้นฐาน)",
            "output": None
        }

    def run_chat_stream(self, message: str):
        """
        Yields tokens from the LLM for a chat message with a strong persona.
        """
        system_prompt = (
            "คุณคือ AetoxOS ระบบปฏิบัติการอัจฉริยะที่พัฒนาโดยทีม Aetox "
            "คุณมีบุคลิกที่เป็นมิตร มืออาชีพ และพร้อมช่วยเหลือผู้ใช้เสมอ "
            "คุณคือ AetoxOS เท่านั้น! ตอบกลับเป็นภาษาไทยเท่านั้นที่สุภาพและเป็นธรรมชาติ"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Stream tokens from Ollama
        for token in self.client.chat_stream(model="qwen2.5:14b", messages=messages):
            yield token
