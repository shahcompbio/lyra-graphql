FROM docker.elastic.co/elasticsearch/elasticsearch:6.5.4
RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install mapper-size
