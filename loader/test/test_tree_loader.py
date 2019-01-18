import pytest
import mock
import networkx as nx
from common.tree_loader import TreeLoader

@pytest.fixture
def tree_loader(mocker):
    mocker.patch('common.utils.es_utils.ElasticSearchTools')
    tree_loader = TreeLoader(es_doc_type="test_doc_type", es_index="test_index", es_host="http://localhost", es_port="9200")

    db_connection = tree_loader.es_tools
    mocker.spy(db_connection, 'submit_data_to_es')
    mocker.spy(db_connection, 'exists_index')
    return tree_loader


NEWICK_FILE = 'example/tree_data.newick'
ROOTED_GML_FILE = 'example/rooted_tree_data.gml'
UNROOTED_GML_FILE = 'example/unrooted_tree_data.gml'
TREE_ORDER_FILE = 'example/tree_order_data.tsv'

def test_get_rooted_tree_newick(tree_loader):
    tree = tree_loader._get_rooted_tree(NEWICK_FILE)
    assert isinstance(tree, nx.DiGraph)
    assert len(list(tree.nodes)) == 6

def test_get_rooted_tree_rooted_gml(tree_loader):
    tree = tree_loader._get_rooted_tree(ROOTED_GML_FILE)
    assert isinstance(tree, nx.Graph)
    assert len(list(tree.nodes)) == 6

def test_get_rooted_tree_unrooted_gml(tree_loader):
    tree = tree_loader._get_rooted_tree(analysis_file=ROOTED_GML_FILE, root_id="ROOT")
    assert isinstance(tree, nx.Graph)
    assert len(list(tree.nodes)) == 6

def test_get_tree_root(tree_loader):
    tree = tree_loader._get_rooted_tree(NEWICK_FILE)
    tree_root = tree_loader._get_tree_root(tree)
    assert tree_root == 'root'

def test_get_tree_ordering_by_descendents(tree_loader):
    tree = tree_loader._get_rooted_tree(NEWICK_FILE)
    tree_root = tree_loader._get_tree_root(tree)
    tree_ordering = tree_loader._get_tree_ordering(tree=tree, tree_root=tree_root)

    assert tree_ordering[tree_root] == ['CELL1','CELL4','LOCI1']
    assert len(tree_ordering['LOCI1']) == len(['CELL2', 'CELL3'])
    assert 'CELL1' not in tree_ordering

def test_get_tree_ordering_by_file(tree_loader):
    tree_ordering = tree_loader._get_tree_ordering(TREE_ORDER_FILE)

    assert tree_ordering['ROOT'] == ['CELL1','CELL4','LOCI1']
    assert len(tree_ordering['LOCI1']) == len(['CELL2', 'CELL3'])
    assert 'CELL1' not in tree_ordering
