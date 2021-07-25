FROM node:current-alpine3.11

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN apk add yarn python make g++ git pandoc

RUN yarn cache clean && yarn --production --frozen-lockfile --non-interactive

CMD node server
