import pytest
import mock
from common.analysis_entry_loader import AnalysisEntryLoader


DASHBOARD = "sample_dashboard"

ANALYSIS_ENTRY_1 = {
    "analysis_id": "abc",
    "dashboard": DASHBOARD
}

ANALYSIS_ENTRY_2 = {
    "analysis_id": "def",
    "dashboard": DASHBOARD
}

@pytest.fixture
def analysis_entry_loader(mocker):
    mocker.patch('common.utils.es_utils.ElasticSearchTools')
    analysis_entry_loader = AnalysisEntryLoader(host="test", port="9200")

    mocker.patch.object(analysis_entry_loader.es_tools, 'search')

    db_connection = analysis_entry_loader.es_tools
    mocker.spy(db_connection, 'delete_record')
    mocker.spy(db_connection, 'submit_to_es')
    mocker.spy(db_connection, 'search')
    mocker.spy(db_connection, 'exists')
    mocker.spy(db_connection, 'create_index')
    yield analysis_entry_loader



def test_init(analysis_entry_loader):
    assert analysis_entry_loader is not None


def test_delete_old_analysis_record_not_exist(analysis_entry_loader):
    analysis_entry_loader._delete_old_analysis_record(ANALYSIS_ENTRY_1, DASHBOARD)
    assert analysis_entry_loader.es_tools.delete_record.call_count == 0

def test_delete_old_analysis_record_exist(mocker, analysis_entry_loader):

    mocker.patch.object(analysis_entry_loader.es_tools, 'search')
    analysis_entry_loader.es_tools.search.return_value = {
        "hits": {
            "total": 1,
            "hits": [ANALYSIS_ENTRY_1]
        }
    }

    analysis_entry_loader._delete_old_analysis_record(ANALYSIS_ENTRY_1, DASHBOARD)
    assert analysis_entry_loader.es_tools.delete_record.call_count == 1


def test_import_file(mocker, analysis_entry_loader):
    mocker.patch.object(analysis_entry_loader.es_tools, 'exists')
    mocker.patch.object(analysis_entry_loader.es_tools, 'refresh_index')
    mocker.patch.object(analysis_entry_loader.es_tools, 'submit_to_es')

    analysis_entry_loader.import_file(ANALYSIS_ENTRY_1, DASHBOARD)
    assert analysis_entry_loader.es_tools.exists.call_count == 1
    assert analysis_entry_loader.es_tools.create_index.call_count == 0
    assert analysis_entry_loader.es_tools.submit_to_es.call_count == 1


# Integration Tests
HOST = 'localhost'
PORT = 9200

def test_analysis_entry_loader():
    analysis_entry_loader = AnalysisEntryLoader(host=HOST, port=PORT)
    assert analysis_entry_loader is not None

    analysis_entry_loader.import_file(ANALYSIS_ENTRY_1, DASHBOARD)
    assert True
    ##assert analysis_entry_loader.es_tools.delete_record.call_count == 0
