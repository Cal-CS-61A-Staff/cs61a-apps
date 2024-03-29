FROM python:3.8-buster

RUN echo "deb https://deb.nodesource.com/node_12.x buster main" > /etc/apt/sources.list.d/nodesource.list
RUN wget -qO- https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list
RUN wget -qO- https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN apt-get update
RUN apt-get install -yqq nodejs yarn
RUN pip install -U pip && pip install pipenv
RUN rm -rf /var/lib/apt/lists/*

RUN wget https://www.openssl.org/source/openssl-1.0.2g.tar.gz -O - | tar -xzpip

RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz
RUN mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /usr/local/gcloud/google-cloud-sdk/install.sh -q
ENV PATH /usr/local/gcloud/google-cloud-sdk/bin:$PATH

RUN gcloud components install beta

RUN apt install -y git
RUN apt-get update && apt-get install -y rsync

RUN apt-get update && apt-get install -y hugo zip

RUN apt-get update && apt-get install -y groff

RUN apt-get update && apt-get install -y pandoc

RUN apt-get update && apt-get install -yqq ruby-full build-essential zlib1g-dev

ENV GEM_HOME $HOME/gems
ENV PATH $HOME/gems/bin:$PATH

RUN gem install jekyll:3.8.5 bundler:1.17.2

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install -r requirements.txt

CMD gunicorn -b :$PORT -w 1 main:app -t 3000
