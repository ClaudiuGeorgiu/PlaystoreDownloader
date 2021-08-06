FROM python:3.9.1-slim-buster

WORKDIR /app/

# Copy requirements and install.
COPY ./Pipfile* /app/
RUN python -m pip install --no-cache-dir --upgrade pip pipenv && \
    pipenv install --deploy --system

# Copy the needed files.
COPY . /app/

# Run with -u $(id -u):$(id -g) to avoid file permission issues.
ENTRYPOINT ["python3", "-m", "cli"]
