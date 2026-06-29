# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY dashboard_server.py .
COPY dashboard.html .
COPY index.html .
COPY generate_qa.py .
COPY rag_evaluation.py .
COPY rag_evaluation_judge.py .
COPY rag_evaluation_qa.json .

# Copy PDF documents
COPY *.pdf ./

# Copy evaluation results if they exist
COPY rag_eval_judge_summary_*.csv ./ 2>/dev/null || true
COPY rag_eval_judge_results_*.json ./ 2>/dev/null || true

# Create directory for ChromaDB
RUN mkdir -p chroma_db

# Expose both ports
EXPOSE 8080 5173

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Start both applications
CMD uvicorn main:app --host 0.0.0.0 --port 8080 & \
    uvicorn dashboard_server:app --host 0.0.0.0 --port 5173 & \
    wait
