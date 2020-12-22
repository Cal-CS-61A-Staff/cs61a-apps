FROM docker.elastic.co/elasticsearch/elasticsearch:7.5.1
ENV discovery.type=single-node
ENV network.host=127.0.0.1

RUN yum -y install centos-release-scl
RUN yum -y install rh-python36

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

SHELL [ "/usr/bin/scl", "enable", "rh-python36" ]
RUN pip install -r requirements.txt
CMD gunicorn --bind :5000 --workers 1 --threads 8 main:app --daemon & /usr/local/bin/docker-entrypoint.sh
