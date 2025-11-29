FROM python:3.11-slim

WORKDIR /app

# 1. Install Dependencies
# Install CPU-only PyTorch first (much smaller download ~150MB vs ~900MB)
# This avoids downloading the full CUDA-enabled PyTorch which is ~900MB
# Note: Only installing API server dependencies (not dashboard dependencies)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=600 --retries=5 \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --timeout=600 --retries=5 \
    fastapi==0.104.1 uvicorn==0.24.0 numpy>=1.24.3 scikit-learn==1.6.1 \
    joblib>=1.3.2 pydantic>=2.5.2

# 2. Copy the Artifacts Folder
# This creates /app/artifacts/ inside the container
COPY artifacts/ ./artifacts/

# 3. Copy the rest of the Application Code
COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]