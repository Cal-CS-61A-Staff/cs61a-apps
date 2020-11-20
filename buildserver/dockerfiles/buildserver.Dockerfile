FROM gcr.io/cs61a-140900/buildserver:latest
#FROM python
#FROM blang/latex:ubuntu
#FROM gcr.io/cs61a-140900/auth:latest

ENV APP_MASTER_SECRET $MASTER_SECRET

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN python highcpu_build.py $APP_NAME $PR_NUMBER $SHA $REPO_ID
