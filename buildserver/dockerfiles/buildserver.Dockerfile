FROM gcr.io/cs61a-140900/website-pr97:latest

ENV APP_MASTER_SECRET $MASTER_SECRET

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN python external_build_worker.py $APP_NAME $PR_NUMBER $SHA $REPO_ID
