# Loaders

A breakdown of the loaders available and the appropriate sections needed for the YAML file. In each dashboard, there is also a sample YAML file.

* [Analysis Entry Loader](#analysis-entry-loader)
* [Tree Loader](#tree-loader)
* [Segments Loader](#segments-loader)
* [Metrics Loader](#metrics-loader)

## Analysis Entry Loader

For each scene, an analysis entry must be loaded with the appropriate metadata.

```
analysis_id:  <ANALYSIS_ID>
jira_id:      <JIRA_ID>
library_id:   <LIBRARY_ID>
description:  <DESCRIPTION>
```

* analysis_id = unique identifier for analysis
* jira_id = JIRA ticket identifier associated with analysis
* library_id = identifier for chip used in analysis
* description = brief outline of sample

## Tree Loader

The tree loader can take in up to three inputs.

```
files:
  tree: /exact/path/to/tree.gml
  tree_order: /exact/path/to/tree_order.tsv
  tree_root: <ROOT_ID>
```

### Tree (Required)

A GML file that contains the nodes and edges for the tree structure.

Requirements:

* Each node must be uniquely labelled
* Must have only one root

### Tree Order (Optional)

A tab-separated file, where each row corresponds to a parent and an array of children. The children are ordered according to the top-to-bottom ordering in the heatmap.

Required columns:

* target = ID of parent node (must match a node in the GML file)
* sources = array of IDs corresponding to children of target (must match nodes in GML file)

NOTE: If no file is provided, the default ordering is by increasing order of descendants.

### Tree Root (Optional)

The ID of the root of the tree. This is only needed if the GML file is undirected. It must correspond to the ID of a node in the GML file.

## Segments Loader

The segment loader can take a list of inputs.

```
files:
  segs:
    - /exact/path/to/segs_01.csv
    - /exact/path/to/segs_02.csv
    - /exact/path/to/segs_03.csv
```

Each file is comma-separated. Each row corresponds to a predicted copy number segment and each column corresponds to an attribute of that segment. Lyra works with the output of HMMcopy, which has been modified for single cell copy number prediction as described in Zahn et al., 2017.

Required columns:

* cell_id = a unique cell identifier
* chr = chromosome number
* start = segment start coordinate
* end = segment end coordinate
* state = integer value of copy number state (e.g. 0, 1, 2, ...)

## Bins Loader

The bins loader can take a list of inputs.

```
files:
  bins:
    - /exact/path/to/bins_01.csv
    - /exact/path/to/bins_02.csv
    - /exact/path/to/bins_03.csv
```

Each file is comma-separated. Each row corresponds to a predicted copy number bin and each column corresponds to an attribute of that bin. Lyra works with the output of HMMcopy, which has been modified for single cell copy number prediction as described in Zahn et al., 2017.

Required columns:

* cell_id = a unique cell identifier
* chr = chromosome number
* start = segment start coordinate
* end = segment end coordinate
* width = number of bases of that bin
* state = integer value of copy number state (e.g. 0, 1, 2, ...)

## Metrics Loader

The metrics loader can take a list of inputs.

```
files:
  metrics:
    - /exact/path/to/metrics_01.csv
    - /exact/path/to/metrics_02.csv
    - /exact/path/to/metrics_03.csv
```

Each file is comma-separated. Each row corresponds to the metrics of a particular cell.

Required columns:

* cell_id = a unique cell identifier
* state_mode = mode of state (related to bins), used for ploidy state
