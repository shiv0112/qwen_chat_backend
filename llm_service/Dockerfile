# Use an official PyTorch image with CUDA support
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Expose FastAPI default port
EXPOSE 8005

# Run Uvicorn
CMD ["uvicorn", "app_v3:app", "--host", "0.0.0.0", "--port", "8005"]
