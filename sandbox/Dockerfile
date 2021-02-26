FROM python:buster

RUN pip install -U pip && pip install pipenv
RUN apt-get update \
  && apt install -y --no-install-recommends texlive-full \
  && apt-get install -y latexmk
RUN apt-get update && apt-get install -y rsync

RUN apt-get install -y curl git vim nginx zip \
  && apt-get install -y make build-essential groff
RUN curl -fsSL https://code-server.dev/install.sh | sh

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update && apt-get install -y yarn
RUN apt-get update && apt-get install -y pandoc

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install -r requirements.txt

CMD python main.py
