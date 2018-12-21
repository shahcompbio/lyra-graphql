# Lyra

[![Build Status](https://travis-ci.org/shahcompbio/lyra-graphql.svg?branch=master)](https://travis-ci.org/shahcompbio/lyra-graphql)

Lyra is a web-based visualization dashboard for single-cell phylogeny.

The front-end is written using [React](https://reactjs.org/) and [Redux](https://redux.js.org/), and uses a [GraphQL](https://graphql.org/) and [ElasticSearch](https://www.elastic.co/) backend.

This repo is for the [GraphQL](https://graphql.org/) backend used for Lyra, which features an [Elasticsearch](https://www.elastic.co/) backend. Python scripts are used to load data into Elasticsearch.

## Documentation

All documentation for Lyra can be found on [https://shahcompbio-lyra.netlify.com](https://shahcompbio-lyra.netlify.com).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- ElasticSearch
- Python 2.7
- pip
- virtualenv
- yarn or npm

### Setting up ElasticSearch

Extract the ElasticSearch archive, and add these to the config/elasticsearch.yml file to enable CORS

```
http.cors.enabled : true
http.cors.allow-origin : "*"
```

Then start the ElasticSearch instance

```
./bin/elasticsearch
```

You can verify that this has been set up correctly by `curl http://localhost:9200` and getting this response:

```
{
  "name" : "",
  "cluster_name" : "",
  "cluster_uuid" : "RsApHfPNQr2SLTQrC9f9Xg",
  "version" : {
    "number" : "6.2.3",
    "build_hash" : "c59ff00",
    "build_date" : "2018-03-13T10:06:29.741383Z",
    "build_snapshot" : false,
    "lucene_version" : "7.2.1",
    "minimum_wire_compatibility_version" : "5.6.0",
    "minimum_index_compatibility_version" : "5.0.0"
  },
  "tagline" : "You Know, for Search"
}
```

### Loading Data

Create a Python 2.7 virtualenv and install the required packages

```
virtualenv ~/pythonenv
source ~/pythonenv/bin/activate
pip install -r <MONTAGE_REPO_DIR>/loader/pip-requires.txt
```

Load using the appropriate dashboard loader with the correct YAML file. For example:

```
python tree_cellscape_loader.py -y directory/to/yaml/data_metadata.yaml
```

This will load an entry into the analysis index, as well as the appropriate data files. You can view the [Loading Docs](https://shahcompbio-lyra.netlify.com/docs/load-overview) to see more information about the data types.

### Setting up graphQL

Clone the [Lyra graphQL](https://github.com/shahcompbio/lyra-graphql) repository and install the necessary dependencies, then start development mode.

```
yarn install
yarn start
```

Following the URL `http://localhost:4000` should bring you to the GraphQL playground, where you can enter queries.
