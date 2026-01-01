FROM python:3.13-slim

WORKDIR /app

# Install MkDocs and all required plugins
RUN pip install --no-cache-dir \
    mkdocs>=1.5.0 \
    mkdocs-material>=9.5.0 \
    mkdocstrings>=0.24.0 \
    mkdocstrings-python>=1.8.0 \
    pymdown-extensions>=10.0

COPY docs ./docs
COPY mkdocs.yml .

EXPOSE 8001

CMD ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8001"]
