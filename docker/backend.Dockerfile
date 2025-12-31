FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock* ./

# Install Python dependencies directly with pip
RUN pip install --no-cache-dir \
    uvicorn[standard] \
    fastapi \
    httpx \
    pydantic \
    pydantic-settings \
    python-dotenv \
    python-multipart \
    aiofiles \
    openai \
    langchain \
    langchain-openai \
    arize-phoenix \
    openinference-instrumentation-langchain \
    openinference-instrumentation-openai \
    polars \
    openpyxl \
    xlrd \
    tiktoken \
    python-pptx

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
