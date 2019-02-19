FROM node:8

RUN apt-get install python2.7
RUN apt-get update && apt-get install -y python-pip
RUN git clone https://github.com/shahcompbio/lyra-graphql.git
RUN cd lyra-graphql && \
  git pull && \
  git checkout docker-build
RUN pip install -r /lyra-graphql/loader/pip-requires.txt
RUN export PYTHONPATH="/lyra-graphql/loader"
CMD python /lyra-graphql/loader/tree_cellscape/tree_cellscape_loader.py -H db -y $YAMLVAR -pp -m
