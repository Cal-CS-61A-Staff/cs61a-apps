FROM python:buster

RUN pip install -U pip && pip install pipenv
RUN apt-get update \
  && apt install -y --no-install-recommends texlive-full \
  && apt-get install -y latexmk
RUN apt-get update && apt-get install -y rsync
RUN curl -fsSL https://code-server.dev/install.sh | sh

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install -r requirements.txt

CMD gunicorn -b :$PORT -w 4 main:app -t 3000
