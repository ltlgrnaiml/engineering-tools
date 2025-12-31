FROM python:3.13-slim

WORKDIR /app

# Install Phoenix
RUN pip install arize-phoenix

ENV PHOENIX_PORT=6006

EXPOSE 6006

CMD ["python", "-m", "phoenix.server.main", "serve"]
