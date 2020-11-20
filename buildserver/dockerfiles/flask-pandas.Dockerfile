FROM python:buster

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install pandas
RUN pip install -r requirements.txt

CMD gunicorn -b :$PORT -w 4 main:app -t 3000
