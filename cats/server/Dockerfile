FROM python:buster

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install -r requirements.txt

CMD gunicorn -b :$PORT -w 1 -t 1 gui:app -t 3000
