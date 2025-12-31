FROM python:3.13-slim

WORKDIR /app

# Install Phoenix and provider SDKs
RUN pip install --no-cache-dir \
    arize-phoenix \
    openai \
    anthropic \
    google-generativeai \
    google-genai \
    boto3

ENV PHOENIX_PORT=6006

EXPOSE 6006

CMD ["python", "-m", "phoenix.server.main", "serve"]
