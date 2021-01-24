FROM python:3.8-slim-buster

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /app

# install requirements into a separate layer
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# copy the code
COPY ./app /app

CMD ["python", "/app/bot.py"]