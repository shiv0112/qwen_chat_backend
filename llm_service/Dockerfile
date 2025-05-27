# Use an official PyTorch image with CUDA support
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel

WORKDIR /app

# Copy everything in llm_service/ to /app
COPY . /app

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Expose FastAPI default port

# Set CUDA and trust flags
ENV CUDA_VISIBLE_DEVICES=1
ENV TRUST_REMOTE_CODE=true

# Start the vLLM OpenAI-compatible server
CMD ["python3", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "./models", \
     "--tokenizer", "./models", \
     "--port", "8005", \
     "--dtype", "float16"]
