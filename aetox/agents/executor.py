import logging
from typing import Dict, List, Any, Optional
from aetox.core.ollama_client import OllamaClient
from aetox.core.prompt_engine import PromptEngine
from aetox.safety.permission import PermissionManager

logger = logging.getLogger("aetox.agents.executor")

class ExecutorAgent:
    """
    Executor Agent - Clean Slate Edition.
    All legacy tools have been removed. Waiting for new tool designs.
    """
    def __init__(self):
        self.client = OllamaClient()
        self.engine = PromptEngine()
        self.permission_manager = PermissionManager()
        # All tools have been disconnected.

    def extract_action(self, task_step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extracts intent. If it's just a conversation, returns 'chat'.
        """
        description = task_step.get("description", "").lower()
        # Heuristic for simple chat
        if any(k in description for k in ["สวัสดี", "hello", "hi", "หวัดดี", "เป็นไงบ้าง"]):
            return {"tool": "chat", "action": "reply", "params": {"message": description}, "confidence": 1.0}
            
        return {"tool": "none", "action": "none", "params": {}, "confidence": 0.0}

    def run_action(self, extraction: Dict[str, Any], memory_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handles 'chat' or reports 'no tools'.
        """
        tool = extraction.get("tool")
        if tool == "chat":
            # Real AI Chat response with strong persona
            system_prompt = (
                "คุณคือ AetoxOS ระบบปฏิบัติการอัจฉริยะที่พัฒนาโดยทีม Aetox "
                "คุณมีบุคลิกที่เป็นมิตร มืออาชีพ และพร้อมช่วยเหลือผู้ใช้เสมอ "
                "คุณคือ AetoxOS เท่านั้น! ตอบกลับเป็นภาษาที่ผู้ใช้ถามที่สุภาพและเป็นธรรมชาติ"
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
            "คุณคือ AetoxOS เท่านั้น! ตอบกลับเป็นภาษาที่ผู้ใช้ถามที่สุภาพและเป็นธรรมชาติ"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Stream tokens from Ollama
        for token in self.client.chat_stream(model="qwen2.5:14b", messages=messages):
            yield token
