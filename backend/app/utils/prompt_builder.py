from app.config import MAX_CONTEXT_LENGTH, MAX_TOKENS, TOKEN_PER_WORD

def estimate_tokens(msgs):
        return int(sum(len(m["content"].split()) * TOKEN_PER_WORD for m in msgs)) 

def build_prompt(
    system_prompt: str,
    history: list,
    max_model_len: int = MAX_CONTEXT_LENGTH,
    reserved_response_tokens: int = MAX_TOKENS
):
    """
    Builds a prompt with a system prompt and trimmed message history based on token usage.
    Ensures the system prompt is never removed. Trims from the top of history if token limit is exceeded.
    """
    available_tokens = max_model_len - reserved_response_tokens
    prompt = [{"role": "system", "content": system_prompt}]

    trimmed = history[:]
    while estimate_tokens(prompt + trimmed) > available_tokens and len(trimmed) > 1:
        trimmed.pop(0)  # drop oldest message from history

    return prompt + trimmed