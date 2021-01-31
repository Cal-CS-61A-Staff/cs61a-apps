FROM python:buster

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN g++ -std=c++17 -O3 main.cpp -o bacon_proj -D CONTEST_RULES=0
RUN g++ -std=c++17 -O3 main.cpp -o bacon -D CONTEST_RULES=1

RUN pip install -r requirements.txt

CMD gunicorn -b :$PORT -w 4 main:app -t 3000
