from app.config import TOKEN_PER_WORD, MAX_CONTEXT_LENGTH, MAX_HISTORY_LEN

def build_prompt(
    system_prompt: str,
    history: list
):
    """
    Builds a prompt by stacking the system prompt and the last `max_history_len` messages from history.
    Does not consider token limits for now, only message count.
    """
    prompt = [{"role": "system", "content": system_prompt}]
    trimmed_history = history[-MAX_HISTORY_LEN:]  # Keep latest N messages
    return prompt + trimmed_history