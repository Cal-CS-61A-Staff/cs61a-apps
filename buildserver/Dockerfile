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
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

RUN gcloud components install beta

RUN apt install -y git
RUN apt-get update && apt-get install -y rsync && apt-get install -y latexmk

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# We run in a venv so that berkeley-cs61a builds don't reinstall all their packages in their own venv

ENV VIRTUAL_ENV /app/env
RUN python -m venv env
ENV PATH $VIRTUAL_ENV/bin:$PATH

RUN pip install -r requirements.txt

# This is because we need the secret at *build* time, not just run time
# This should be avoided when possible, so it's not in e.g. flask.Dockerfile
# Cloud Run will inject the secret into the container at run time
ENV APP_MASTER_SECRET <APP_MASTER_SECRET>

# We cache the website git repo so that we can just fetch it, rather than doing a full clone for every build
# This is just a performance optimization for a common dependency, and is not necessary for smaller repos we depend on
RUN mkdir repos
RUN python -c "from common.rpc.secrets import get_secret; print(get_secret(secret_name=\"GITHUB_ACCESS_TOKEN\"))" > github_access_token
RUN git clone https://$(cat github_access_token)@github.com/Cal-CS-61A-Staff/berkeley-cs61a repos/Cal-CS-61A-Staff-berkeley-cs61a
RUN pip install -r Cal-CS-61A-Staff-berkeley-cs61a/requirements.txt

CMD gunicorn -b :$PORT -w 1 main:app -t 3000
