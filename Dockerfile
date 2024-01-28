FROM python:3.9

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /code

# install cryptography requirements
RUN apt update && apt install -y rustc cargo

# install dependencies
RUN pip install --upgrade pip && pip install "setuptools<58.0.0"
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# is the codez
COPY ./src/ /code/

# Tests the codez
COPY coverage.sh /code/
RUN chmod +x coverage.sh

# Some stuipid webserver bs ;)
COPY uwsgi.conf /code/

RUN mkdir /code/static
RUN mkdir /code/staticfiles
RUN mkdir /code/mediafiles

VOLUME /code/static
VOLUME /code/mediafiles


EXPOSE 8000

#CMD ["python", "/code/manage.py", "runserver", "0.0.0.0:8000"]