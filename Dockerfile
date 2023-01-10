FROM python:3.8-slim-buster

ARG initial_otp

WORKDIR flask-server/

COPY requirements.txt .
COPY app.py .
COPY models.py .
COPY .env .
COPY templates templates
COPY static static
COPY initialize_database.sh .

RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get install -y sqlite3 libsqlite3-dev

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r ./requirements.txt

RUN flask db init --directory ./migrations \
    && flask db migrate \
    && flask db upgrade

RUN ./initialize_database.sh

CMD ["python", "app.py"]