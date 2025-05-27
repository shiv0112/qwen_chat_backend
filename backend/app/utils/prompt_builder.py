from app.config import DEFAULT_SYSTEM_PROMPT, MAX_CONTEXT_LENGTH, MAX_TOKENS

def count_tokens(messages: list) -> int:
    # Simple approximation: 1 word = 1.3 tokens, adjust based on real tokenizer if needed
    total = 0
    for msg in messages:
        total += int(len(msg["content"].split()) * 1.3)
    return total


def build_prompt(system_prompt: str, messages: list, max_model_len: int = MAX_CONTEXT_LENGTH, reserved_response_tokens: int = MAX_TOKENS):
    """
    Builds a trimmed prompt including system prompt and latest messages
    that fits within the context window.
    """
    prompt = [{"role": "system", "content": system_prompt}]
    available_tokens = max_model_len - reserved_response_tokens

    # Reverse messages to keep latest messages and add until we exceed context
    total_tokens = count_tokens(prompt)
    retained_messages = []

    for msg in reversed(messages):
        msg_tokens = count_tokens([msg])
        if total_tokens + msg_tokens > available_tokens:
            break
        retained_messages.insert(0, msg)
        total_tokens += msg_tokens

    prompt.extend(retained_messages)
    return prompt
