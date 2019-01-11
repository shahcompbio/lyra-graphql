import pytest
import mock
import pandas as pd
from common.segs_loader import SegsLoader

CSV_FILE = 'example/segs_data.csv'


@pytest.fixture
def segs_loader(mocker):
    mocker.patch('common.utils.es_utils.ElasticSearchTools')
    segs_loader = SegsLoader(es_doc_type="test_doc_type", es_index="test_index", es_host="http://localhost", es_port="9200")

    db_connection = segs_loader.es_tools
    mocker.spy(db_connection, 'submit_df_to_es')
    mocker.spy(db_connection, 'exists_index')
    return segs_loader

def test_init(segs_loader):
    assert segs_loader is not None

def test_read_file_csv(segs_loader):
    data = segs_loader._read_file(CSV_FILE)
    assert isinstance(data, pd.DataFrame)

def test_transform_data(segs_loader):
    data = segs_loader._read_file(CSV_FILE)
    data = segs_loader._transform_data(data)

    field_mappings = segs_loader.__field_mapping__

    for field in field_mappings:
        print "\nField mapping: %s to %s" % (field, field_mappings[field])
        assert not field in data.columns
        assert field_mappings[field] in data.columns

def test_load_segs_table(segs_loader):
    data = segs_loader._read_file(CSV_FILE)
    data = segs_loader._transform_data(data)
    segs_loader._load_segs_table(data)

    segs_loader.es_tools.exists_index.assert_called_once_with()
    segs_loader.es_tools.submit_df_to_es.assert_called_once_with(data)
