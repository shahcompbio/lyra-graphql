# Loading - Clonescape

Clonescape requires:

* [Tree data](../commmon/README.md#tree-loader)
* [Segment data](../commmon/README.md#segments-loader)
* [Bin data](../commmon/README.md#bins-loader)

## Sample YAML file

```
analysis_id:  <ANALYSIS_ID>
jira_id:      <JIRA_ID>
library_id:   <LIBRARY_ID>
description:  <DESCRIPTION>
files:
  tree: /exact/path/to/rooted_tree.gml
  tree_order: /exact/path/to/tree_order.tsv
  segs:
    - /exact/path/to/segs_01.csv
    - /exact/path/to/segs_02.csv
    - /exact/path/to/segs_03.csv
  bins:
    - /exact/path/to/bins_01.csv
    - /exact/path/to/bins_02.csv
    - /exact/path/to/bins_03.csv
```

## Loading Data

1. Make sure the required virtual environment and dependencies are installed.

```
virtualenv ~/pythonenv
source ~/pythonenv/bin/activate
pip install -r <DIRECTORY>/install/pip-requires.txt
```

2. Run the main loader, which will load all the data according to the exact paths within the YAML file

```
python tree_clonescape_loader.py -y /exact/path/to/analysis_metadata_yaml.yaml
```
