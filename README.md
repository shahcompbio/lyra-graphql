# Lyra

[Lyra](https://github.com/shahcompbio/lyra) is a web-based visualization platform, featuring several interactive dashboards of single cell genomics data.

This repo is for the [GraphQL](https://graphql.org/) backend used for Lyra, which features an [Elasticsearch](https://www.elastic.co/) backend. Python scripts are used to load data into Elasticsearch.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* ElasticSearch
* Python 2.7
* pip
* virtualenv
* yarn or npm

### Installing

Extract the ElasticSearch archive, and add these to the config/elasticsearch.yml file to enable CORS

```
http.cors.enabled : true
http.cors.allow-origin : "*"
```

Also install the mapper-size plugin

```
./bin/elasticsearch-plugin install mapper-size
```

Then start the ElasticSearch instance

```
./bin/elasticsearch
```

Clone the repository and install the necessary dependencies, then start development mode.

```
yarn install
yarn start
```

### Loading Data

Create a Python virtualenv and install the required packages

```
virtualenv ~/pythonenv
source ~/pythonenv/bin/activate
pip install -r <MONTAGE_REPO_DIR>/loader/pip-requires.txt
```

Load using the appropriate dashboard loader with the correct YAML file. For example:

```
python tree_cellscape_loader.py -y directory/to/yaml/data_metadata.yaml
```

This will load an entry into the Analysis index, as well as the appropriate data files. You can view the [README in /loader](./loader/common/README.md) to see more information about the data types.
