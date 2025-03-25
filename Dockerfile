FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1

ENV APP_DIR=/usr/src/app

WORKDIR $APP_DIR

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY ./ ${APP_DIR}

# Install the application dependencies.
RUN uv pip install --system -e .

# Make port 8000 available
EXPOSE 8000

# Run the application (path corrected to use the proper venv location)
CMD ["uvicorn", "app.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]