FROM python: 3.11-slim

WORKDIR /app

# 1. Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the Artifacts Folder
# This creates /app/artifacts/ inside the container
COPY artifacts/ ./artifacts/

# 3. Copy the rest of the Application Code
COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]