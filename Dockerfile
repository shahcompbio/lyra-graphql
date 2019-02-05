FROM docker.elastic.co/elasticsearch/elasticsearch:6.5.4

RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install mapper-size

RUN yum -y install sudo

RUN curl --silent --location https://rpm.nodesource.com/setup_8.x | sudo bash - && \
  curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo && \
  sudo yum -y install yarn && \
  npm install pm2@latest -g

RUN sudo yum -y install git

RUN git clone https://github.com/shahcompbio/lyra-graphql.git && \
  cd lyra-graphql && \
  yarn install && \
  yarn build && \
  pm2 start lib/index.js && \
  pm2 ls && \
  cd ..

RUN git clone https://github.com/shahcompbio/lyra.git && \
  cd lyra && \
  git pull && \
  yarn install

EXPOSE 4000
EXPOSE 3000

CMD pm2 start /usr/local/bin/docker-entrypoint.sh && \
  pm2 start lyra-graphql/lib/index.js && \
  cd lyra && \
  yarn start;
