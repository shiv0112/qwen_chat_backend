import asyncio
import traceback
from vllm import LLM, SamplingParams
from fastapi.responses import StreamingResponse
from typing import List, AsyncGenerator
from app.config import MODEL_PATH, STOP_SEQUENCES
from app.schemas.generate_schemas import GenRequest, GenChunk
from app.services.prompt_builder import chat_messages_to_qwen_prompt

llm = LLM(model=MODEL_PATH, dtype="auto")

async def generate_response(req: GenRequest):
    try:
        prompt_string = chat_messages_to_qwen_prompt(req.messages)
    except Exception as e:
        traceback.print_exc()
        raise ValueError(f"Invalid messages: {str(e)}")

    prompts = [prompt_string]
    stop_seq = req.stop if req.stop is not None else STOP_SEQUENCES

    sampling_params = SamplingParams(
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
        stop=stop_seq,
        top_k=req.top_k,
        repetition_penalty=req.repetition_penalty
    )

    if not req.stream:
        outputs = await asyncio.get_event_loop().run_in_executor(
            None, lambda: llm.generate(prompts, sampling_params)
        )
        text = outputs[0].outputs[0].text.split("<|im_end|>")[0]
        return {"text": text}

    async def token_stream() -> AsyncGenerator[str, None]:
        prev_text = ""
        try:
            for output in llm.generate(prompts, sampling_params):
                text = output.outputs[0].text
                if "<|im_end|>" in text:
                    text = text.split("<|im_end|>")[0]
                new_text = text[len(prev_text):]
                prev_text = text
                if new_text:
                    yield GenChunk(token=new_text).json() + "\n"
        except Exception as e:
            yield f'{{"error": "{str(e)}"}}\n'

    return StreamingResponse(token_stream(), media_type="application/jsonlines")
