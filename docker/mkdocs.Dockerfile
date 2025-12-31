FROM python:3.13-slim

WORKDIR /app

# Install MkDocs and plugins
RUN pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python

COPY docs ./docs
COPY mkdocs.yml .

EXPOSE 8001

CMD ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8001"]
