# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy app code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Chainlit port
# EXPOSE 8000

# Run Chainlit app
# CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]