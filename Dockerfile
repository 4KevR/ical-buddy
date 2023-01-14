FROM python:3.8-slim-buster

ARG initial_otp

WORKDIR flask-server/

COPY requirements.txt .
COPY app.py .
COPY app.ini .
COPY models.py .
COPY .env .
COPY templates templates
COPY static static
COPY initialize_database.sh .
COPY container_start_script.sh .

RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get install -y sqlite3 libsqlite3-dev build-essential

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r ./requirements.txt \
    && pip install uwsgi

RUN flask db init --directory ./migrations \
    && flask db migrate \
    && flask db upgrade

RUN ./initialize_database.sh

CMD ["bash", "./container_start_script.sh"]