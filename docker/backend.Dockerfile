FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock* ./

# Install Python dependencies directly with pip
# Core dependencies
RUN pip install --no-cache-dir \
    uvicorn[standard] \
    fastapi \
    httpx \
    pydantic \
    pydantic-settings \
    python-dotenv \
    python-multipart \
    aiofiles \
    aiosqlite \
    polars \
    pyarrow \
    beautifulsoup4 \
    pyyaml \
    psutil \
    jsonpath-ng

# AI/LLM dependencies
RUN pip install --no-cache-dir \
    openai \
    langchain \
    langchain-openai \
    langgraph \
    tiktoken \
    sentence-transformers

# Observability
RUN pip install --no-cache-dir \
    arize-phoenix \
    arize-phoenix-otel \
    openinference-instrumentation-langchain \
    openinference-instrumentation-openai

# PPTX Generator dependencies
RUN pip install --no-cache-dir \
    python-pptx \
    matplotlib \
    pillow \
    pandas \
    openpyxl \
    xlrd

# SOV Analyzer dependencies
RUN pip install --no-cache-dir \
    scipy \
    statsmodels \
    numpy

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
