'''
Parser/Indexer for tree files

Required:
* .gml file
* [OPTIONAL] root name
* [OPTIONAL] .tsv ordering file


'''

import csv
import ast
import re
import copy
import logging
import argparse
import os
import sys
import math
import __builtin__
import networkx as nx
import pandas as pd

from Bio import Phylo
from networkx.algorithms.traversal.depth_first_search import dfs_tree
from utils.analysis_loader import AnalysisLoader


class TreeLoader(AnalysisLoader):

    ''' Class TreeLoader '''

    def __init__(
            self,
            es_doc_type=None,
            es_index=None,
            es_host=None,
            es_port=None,
            use_ssl=False,
            http_auth=None,
            timeout=None):
        super(TreeLoader, self).__init__(
            es_doc_type=es_doc_type,
            es_index=es_index,
            es_host=es_host,
            es_port=es_port,
            use_ssl=use_ssl,
            http_auth=http_auth,
            timeout=timeout)

    def load_file(self, analysis_file=None, ordering_file=None, root_id=None, tree_edges=None):
        if self.es_tools.exists_index():
            logging.info('Tree data for analysis already exists - will delete old index')
            self.es_tools.delete_index()

        self.create_index()

        self.disable_index_refresh()
        tree = self._get_rooted_tree(analysis_file, root_id, tree_edges)

        tree_root = self._get_tree_root(tree)

        ordering = self._get_tree_ordering(ordering_file, tree, tree_root)

        self._load_tree_data(tree, ordering, tree_root)

        self.enable_index_refresh()



    def _get_rooted_tree(self, analysis_file, root_id, tree_edges):
        # load graph from newick
        if analysis_file.endswith('.newick'):
            newick_tree = Phylo.read(analysis_file, 'newick')
            graph = Phylo.to_networkx(newick_tree)

            new_graph = nx.Graph()
            for edge in graph.edges():
                new_graph.add_edge(format_name(str(edge[0]).strip()), format_name(str(edge[1]).strip()))

            tree = nx.dfs_tree(new_graph, 'root')


        # GML with root name
        elif root_id is not None:
            graph = nx.read_gml(analysis_file)
            new_graph = nx.Graph()

            for edge in graph.edges():
                new_graph.add_edge(edge[0], edge[1])

            tree = nx.dfs_tree(new_graph, root_id)
        # already rooted GML
        elif analysis_file is not None:
            original_tree = nx.read_gml(analysis_file)
            tree = nx.DiGraph()

            for edge in original_tree.edges():
                tree.add_edge(str(edge[0]).strip(), str(edge[1]).strip())

        # tree edges
        else:
            tree = nx.DiGraph()

            with open(tree_edges) as csv_in:
                csv_reader = csv.DictReader(csv_in)
                for row in csv_reader:
                    tree.add_edge(row['source'].strip(), row['target'].strip())

        return tree


    def _get_tree_root(self, tree):
        all_nodes = list(tree.nodes)
        [tree_root] = [n for n in all_nodes if tree.in_degree(n)==0]

        return tree_root




    def _get_tree_ordering(self, ordering_file, tree, tree_root):


        def _count_descendents(node):
            try:
                descendent_count = len(nx.descendants(tree, node)) + 1
                return descendent_count
            except KeyError:
                return 0

        ordering = {}

        if ordering_file is not None:
            with open(ordering_file) as tsv_in:
                tsv_in = csv.reader(tsv_in, delimiter='\t')

                for row in tsv_in:
                    ordering[row[0].strip()] = [child.strip() for child in row[1].split(',')]

        else:
            todo_list = [tree_root]

            while todo_list != []:
                curr_node = todo_list.pop(0)

                curr_children = nx.dfs_successors(tree, curr_node, 1)

                if curr_children != {}:
                    curr_children = curr_children[curr_node]
                    curr_children.sort(key=_count_descendents)
                    ordering[curr_node.strip()] = [child.strip() for child in curr_children]

                    todo_list = curr_children + todo_list

        return ordering



    def _load_tree_data(self, tree, ordering, tree_root):

        todo_list = [[tree_root, 'root']]
        heatmap_index = 0
        data = []

        while todo_list != []:
            [curr_node, curr_parent] = todo_list.pop(0)
            unmerged_id = curr_node
            max_height = self._get_max_height_from_node(tree, curr_node)
            
            if max_height != 0:

                num_leaf_descendants = self._get_number_of_leaf_descendants(curr_node, tree)

                curr_node, ordering = self._merge_if_child_is_single_internal_node(curr_node, ordering)

                curr_children = ordering[curr_node]

                index_record = {
                    'cell_id': curr_node,
                    'unmerged_id': unmerged_id,
                    'parent': curr_parent,
                    'children': curr_children,
                    'max_height': max_height,
                    'min_index': heatmap_index,
                    'max_index': heatmap_index + num_leaf_descendants - 1
                }

                data = data + [index_record]
                todo_list = [[child, curr_node] for child in curr_children] + todo_list


            else: #is leaf node
                curr_children = []
                index_record = {
                    'heatmap_order': heatmap_index,
                    'cell_id': curr_node,
                    'unmerged_id': unmerged_id,
                    'parent': curr_parent,
                    'children': [],
                    'max_height': 0,
                    'min_index': heatmap_index,
                    'max_index': heatmap_index
                }

                data = data + [index_record]
                heatmap_index += 1


            logging.debug(index_record)

        # Submit any records remaining in the buffer for indexing

        data_table = pd.DataFrame(data)
        self.es_tools.submit_df_to_es(data_table)




    def _get_max_height_from_node(self, tree, node):
        try:
            path_lengths = nx.shortest_path_length(tree, source=node)
            node_with_longest_path = max(path_lengths.keys(), key=lambda key: path_lengths[key])

            return path_lengths[node_with_longest_path]
        except KeyError:
            return 0




    def _merge_if_child_is_single_internal_node(self, curr_node, ordering):
        curr_children = ordering[curr_node]

        # if only one child
        if len(curr_children) == 1:
            try:
                # check if child is a leaf node
                curr_gchildren = ordering[curr_children[0]]
                # if not, merge node and its single child
                curr_node = curr_node + ", " + curr_children[0]
                ordering[curr_node] = curr_gchildren
                return self._merge_if_child_is_single_internal_node(curr_node, ordering)
            except KeyError:
                return (curr_node, ordering)
        else:
            return (curr_node, ordering)




    def _get_number_of_leaf_descendants(self, curr_node, tree):
        subtree = dfs_tree(tree, curr_node)
        sub_nodes = list(subtree.nodes)
        return len([n for n in sub_nodes if subtree.out_degree(n)==0])



def format_name(str):
    strs = str.split('_')
    if strs[0] == 'cell':
        return strs[1]
    else:
        return str



def get_args():
    '''
    Argument parser
    '''
    parser = argparse.ArgumentParser(
        description=('Creates an index in Elasticsearch for tree node data and parses appropriate gml file')
    )
    required_arguments = parser.add_argument_group("required arguments")
    parser.add_argument(
        '-i',
        '--index',
        dest='index',
        action='store',
        help='Index name',
        type=str)
    parser.add_argument(
        '-g',
        '--gml_file',
        dest='gml_file',
        action='store',
        help='Tree data file',
        type=str)
    parser.add_argument(
        '-or',
        '--ordering_file',
        dest='ordering_file',
        action='store',
        help='Ordering file for tree',
        type=str)

    parser.add_argument(
        '-r',
        '--root',
        dest='root_id',
        action='store',
        help='Cell ID for root node',
        type=str)
    parser.add_argument(
        '-ed',
        '--edges',
        dest='tree_edges',
        action='store',
        help='CSV file of tree edges',
        type=str)
    parser.add_argument(
        '-H',
        '--host',
        default='localhost',
        metavar='Host',
        help='The Elastic search server hostname.')
    parser.add_argument(
        '-p',
        '--port',
        default=9200,
        metavar='Port',
        help='The Elastic search server port.')
    parser.add_argument(
        '--use-ssl',
        dest='use_ssl',
        action='store_true',
        help='Connect over SSL',
        default=False)
    parser.add_argument(
        '-u',
        '--username',
        dest='username',
        help='Username')
    parser.add_argument(
        '-P',
        '--password',
        dest='password',
        help='Password')
    parser.add_argument(
        '-v',
        '--verbosity',
        dest='verbosity',
        action='store',
        help='Default level of verbosity is INFO.',
        choices=['info', 'debug', 'warn', 'error'],
        type=str,
        default="info")
    return parser.parse_args()

def _set_logger_config(verbosity=None):
    # Set logging to console, default verbosity to INFO.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        stream=sys.stdout
    )

    if verbosity:
        if verbosity.lower() == "debug":
            logger.setLevel(logging.DEBUG)

        elif verbosity.lower() == "warn":
            logger.setLevel(logging.WARN)

        elif verbosity.lower() == "error":
            logger.setLevel(logging.ERROR)

def main():
    args = get_args()
    _set_logger_config(args.verbosity)
    es_loader = TreeLoader(
        es_doc_type=args.index,
        es_index=args.index,
        es_host=args.host,
        es_port=args.port)

    es_loader.load_file(analysis_file=args.gml_file, ordering_file=args.ordering_file, root_id=args.root_id, tree_edges=args.tree_edges)




if __name__ == '__main__':
    main()
