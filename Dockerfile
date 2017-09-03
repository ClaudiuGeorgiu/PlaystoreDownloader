FROM python:3.6.2

# Copy requirements and install
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt

# Copy the needed files
COPY ./playstore /app/playstore
COPY ./download.py /app/
COPY ./credentials.json /app/

CMD ["python3", "/app/download.py"]
