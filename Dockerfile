FROM python:3.10

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /code

# install dependencies
RUN pip install --upgrade pip 
COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY ./trunkplayerNG/ /code/

EXPOSE 8000

#CMD ["python", "/code/manage.py", "runserver", "0.0.0.0:8000"]