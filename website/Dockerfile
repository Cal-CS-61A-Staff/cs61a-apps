FROM python:3.8-buster

RUN pip install -U pip && pip install pipenv
RUN rm -rf /var/lib/apt/lists/*

# This image is used to *build* the website, not just *host* it, which is why it
# has some random things. Latex builds

RUN apt install -y git
RUN apt-get update && apt-get install -y rsync && apt-get install -y latexmk

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install -r requirements.txt

CMD gunicorn -b :$PORT -w 8 main:app -t 3000
