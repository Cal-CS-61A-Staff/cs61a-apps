FROM python:buster

RUN pip install -U pip && pip install pipenv
RUN apt-get update \
 && apt-get install -y curl git vim nginx make build-essential
# && apt install -y --no-install-recommends texlive-full \  @nocommit
# && apt-get install -y latexmk                             @nocommit
# RUN apt-get update && apt-get install -y rsync            @nocommit
RUN curl -fsSL https://code-server.dev/install.sh | sh

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install -r requirements.txt

CMD python main.py
