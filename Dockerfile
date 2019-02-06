FROM node:8 as react-build

RUN npm install http-server -g

RUN git clone https://github.com/shahcompbio/lyra.git && \
  cd lyra && \
  git pull && \
  yarn install && \
  yarn build && \
  ls -l && \
  pwd


FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY —-from=react-build /lyra/build /usr/share/nginx/html
EXPOSE 80
CMD [“nginx”, “-g”, “daemon off;”]
