FROM python:3.6.2

# Copy requirements and install
RUN mkdir /app
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt

# Copy the needed files
COPY ./playstore /app/playstore
COPY ./download.py /app/
COPY ./credentials.json /app/

WORKDIR /app

# Run with -u $(id -u):$(id -g) to avoid file permission issues
ENTRYPOINT ["python3", "/app/download.py"]
