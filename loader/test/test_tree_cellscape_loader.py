import mock
import pytest
from common.analysis_entry_loader import AnalysisEntryLoader
from tree_cellscape.tree_cellscape_loader import load_analysis_entry


def test_load_analysis_entry(mocker):
    MockAnalysisEntryLoader = mocker.patch('common.analysis_entry_loader.AnalysisEntryLoader')
    yaml_data = mock.Mock()
    args = mock.Mock()
    args.host = 'localhost'
    args.port = 9200
    MockAnalysisEntryLoader.return_value.import_file.return_value = 1
    load_analysis_entry(args, yaml_data)
    MockAnalysisEntryLoader.assert_called_once_with(args.host, args.port)

def test_load_analysis_entry2():
    with mock.patch('common.utils.es_utils.ElasticSearchTools') as MockElasticSearchTools:
        analysis_loader = AnalysisEntryLoader(host='localhost', port=9200)

        assert True
