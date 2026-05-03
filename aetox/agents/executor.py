import logging
import os
from typing import Dict, List, Any, Optional
from aetox.core.ollama_client import OllamaClient
from aetox.core.prompt_engine import PromptEngine
from aetox.safety.permission import PermissionManager
from aetox.tools.file_manager import MasterFileManager
from aetox.tools.vision import AetoxVision
from aetox.tools.system_control import SystemControl

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
        self.system = SystemControl()
        self.last_path = None
        self.history = [] # Rolling buffer of last 3 interactions

    def add_to_history(self, question: str, answer: str):
        """Adds a Q&A pair to history, keeping only the last 3 and truncating to 200 chars."""
        q_trunc = question[:200]
        a_trunc = answer[:200] if isinstance(answer, str) else str(answer)[:200]
        self.history.append({"q": q_trunc, "a": a_trunc})
        if len(self.history) > 3:
            self.history.pop(0)

    def _get_tools_info(self) -> str:
        """Dynamically gathers name and description from all registered tools."""
        tools = [self.file_manager, self.vision, self.system]
        info = ""
        for i, tool in enumerate(tools):
            info += f"{i+1}. {tool.name}: {tool.description}\n"
        return info

    def extract_action(self, task_step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uses LLM to extract intent with dynamic tool discovery and rolling history.
        """
        description = task_step.get("description", "")
        
        # Format history for prompt
        history_str = ""
        for i, h in enumerate(self.history):
            history_str += f"{i+1}. ถาม: {h['q']} -> ตอบ: {h['a']}\n"

        # Load template and inject dynamic tools info
        prompt_data = self.engine.get_external_template("config/prompts/executor.yaml", "intent_extraction")
        
        system_msg = prompt_data.get("system_template", "").format(
            tools=self._get_tools_info(),
            history=history_str or "ไม่มี",
            last_path=self.last_path or "ยังไม่มี"
        )
        user_msg = prompt_data.get("user_input_template", "").format(description=description)

        # Extraction using Ollama
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        try:
            result = self.client.chat(model="qwen2.5:14b", messages=messages, format="json")
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
            result = self.vision.execute(params)
            # If it's a successful read and user asked for summary, wrap it with LLM summary
            if result.get("status") == "success" and "raw_text" in result:
                # Decide if we need to summarize based on intent
                if action == "summarize" or any(k in description for k in ["สรุป", "summary"]):
                    summary_prompt = (
                        "คุณคือผู้เชี่ยวชาญด้านการสรุปข้อมูล (Super Summarizer)\n"
                        "หน้าที่ของคุณคือ: อ่านข้อความต่อไปนี้แล้วสรุปแบบ 'ขั้นสุด' (สั้น กระชับ ตรงประเด็น)\n"
                        "ไม่ต้องอ่านเนื้อหาให้ฟัง! ให้บอกแค่ว่า 'เอกสารนี้เกี่ยวกับอะไร' เท่านั้น\n\n"
                        f"เนื้อหาจากไฟล์:\n{result['raw_text'][:8000]}\n\n"
                        "สรุปแบบขั้นสุด (ภาษาไทย):"
                    )
                    res = self.client.chat(model="qwen2.5:14b", messages=[{"role": "user", "content": summary_prompt}])
                    summary_text = res.get("message", {}).get("content", "สรุปไม่ได้ครับ")
                    result["output"] = f"👁️ **[AetoxVision - Super Summary]**\n\n{summary_text}"
            
            return result

        if tool == "system_control":
            return self.system.execute(params)

        if tool == "chat":
            # Real AI Chat response with strong persona
            system_prompt = (
                "คุณคือ AetoxOS ระบบปฏิบัติการอัจฉริยะที่พัฒนาโดยทีม Aetox "
                "คุณมีบุคลิกที่เป็นมิตร มืออาชีพ และพร้อมช่วยเหลือผู้ใช้เสมอ "
                "คุณคือ AetoxOS เท่านั้น! ตอบกลับเป็นภาษาไทยเท่านั้นที่สุภาพและเป็นธรรมชาติ"
            )
            # Include history for chat context
            history_messages = []
            for h in self.history:
                history_messages.append({"role": "user", "content": h["q"]})
                history_messages.append({"role": "assistant", "content": h["a"]})

            messages = [
                {"role": "system", "content": system_prompt},
                *history_messages,
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
