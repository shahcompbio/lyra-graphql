FROM node:8

RUN npm install pm2@latest -g

RUN git clone https://github.com/shahcompbio/lyra-graphql.git && \
  cd lyra-graphql && \
  yarn install && \
  yarn build

EXPOSE 4000

CMD node lyra-graphql/lib/index.js
