FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
WORKDIR /app
# uv.lock comes from the lab's setup at founding; README.md is the package's readme (pyproject)
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD ["uv", "run", "--frozen", "--no-dev", "python", "-m", "mixed_method_ontology"]
