FROM python:3.8.2-slim-buster

WORKDIR /app/

# Copy requirements and install.
COPY ./requirements.txt /app/
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the needed files.
COPY . /app/

# Run with -u $(id -u):$(id -g) to avoid file permission issues.
ENTRYPOINT ["python3", "download.py"]
