FROM python:3.8.0-slim-buster

WORKDIR /app

# Copy requirements and install.
COPY requirements.txt /app
RUN python3.8 -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the needed files.
COPY ./playstore /app/playstore
COPY ./download.py /app/
COPY ./credentials.json /app/

# Run with -u $(id -u):$(id -g) to avoid file permission issues.
ENTRYPOINT ["python3.8", "/app/download.py"]
