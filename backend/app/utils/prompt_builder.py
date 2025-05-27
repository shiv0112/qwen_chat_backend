from app.config import MAX_CONTEXT_LENGTH, MAX_TOKENS

def build_prompt(system_prompt: str, messages: list, session_tokens_used: int, max_model_len: int = MAX_CONTEXT_LENGTH, reserved_response_tokens: int = MAX_TOKENS):
    """
    Builds a trimmed prompt using already tracked session token usage.
    Removes older messages until the total token count is within the model's context limit.
    """
    available_tokens = max_model_len - reserved_response_tokens
    prompt = [{"role": "system", "content": system_prompt}]

    # If tokens used so far exceeds available tokens, we trim messages
    if session_tokens_used > available_tokens:
        # Approximate average tokens per message
        avg_tokens_per_msg = session_tokens_used // len(messages) if messages else 0
        tokens_to_trim = session_tokens_used - available_tokens
        messages_to_trim = (tokens_to_trim // avg_tokens_per_msg) + 1 if avg_tokens_per_msg else 0
        messages = messages[messages_to_trim:]  # keep latest

    return prompt + messages
