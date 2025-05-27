from typing import List, Dict
from app.config import SYSTEM_PROMPT

def chat_messages_to_qwen_prompt(messages: List[Dict[str, str]]) -> str:
    prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
    for msg in messages:
        role = msg.get("role", "").strip().lower()
        content = msg.get("content", "")

        if role in {"user", "assistant"}:
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt
