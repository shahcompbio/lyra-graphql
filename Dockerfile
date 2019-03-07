FROM node:8

WORKDIR /usr/src/app

COPY package*.json ./
RUN yarn install

COPY /lib ./lib
RUN ls


EXPOSE 4000

CMD node lib/index.js
