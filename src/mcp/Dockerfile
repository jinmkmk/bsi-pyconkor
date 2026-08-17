FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY lunch_mcp ./lunch_mcp
RUN pip install --no-cache-dir .

EXPOSE 8001
CMD ["school-lunch-mcp"]
