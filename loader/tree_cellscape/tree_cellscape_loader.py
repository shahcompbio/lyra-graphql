
import logging
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from common.analysis_entry_loader import AnalysisEntryLoader
from common.yaml_data_parser import YamlData
from common.tree_loader import TreeLoader
from common.segs_loader import SegsLoader
from common.metrics_loader import MetricsLoader
from common.bins_loader import BinsLoader
from common.normalize_segs import normalize_segs
from common.preprocessor import Preprocessor

dashboard_type = "TREE_CELLSCAPE"


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


def load_analysis_entry(args, yaml_data):
    logging.info("")
    logging.info("")
    logging.info("==================")
    logging.info("LOADING ANALYSIS ENTRY")
    logging.info("==================")
    analysis_loader = AnalysisEntryLoader(
        host=args.host,
        port=args.port
    )
    record = yaml_data.get_analysis_entry(dashboard_type)
    analysis_loader.import_file(record, dashboard_type)
    logging.info("Analysis entry loaded")
    sys.stdout.flush()
    print(record+"-AnalysisDone")
    sys.stdout.flush()

def load_tree_data(args, yaml_data):
    logging.info("")
    logging.info("")
    logging.info("==================")
    logging.info("LOADING TREE DATA")
    logging.info("==================")
    index_name = yaml_data.get_index_name(dashboard_type, "tree")

    tree_loader = TreeLoader(
        es_doc_type=index_name,
        es_index=index_name,
        es_host=args.host,
        es_port=args.port
    )

    tree_loader.load_file(
        analysis_file=yaml_data.get_file_paths("tree"),
        ordering_file=yaml_data.get_file_paths("tree_order"),
        root_id=yaml_data.get_file_paths("tree_root"),
        tree_edges=yaml_data.get_file_paths("tree_edges")
    )
    sys.stdout.flush()
    print(yaml_data.get_file_paths("tree")+"-TreeDone")
    sys.stdout.flush()

def load_segs_data(args, yaml_data):
    logging.info("")
    logging.info("")
    logging.info("==================")
    logging.info("LOADING SEGS DATA")
    logging.info("==================")
    index_name = yaml_data.get_index_name(dashboard_type, "segs")

    segs_loader = SegsLoader(
        es_doc_type=index_name,
        es_index=index_name,
        es_host=args.host,
        es_port=args.port
    )

    seg_files = yaml_data.get_file_paths("segs")

    if segs_loader.es_tools.exists_index():
        logging.info('Seg data for analysis already exists - will delete old index')
        segs_loader.es_tools.delete_index()

    if seg_files is not None:
        for seg_file in seg_files:
            segs_loader.load_file(
                analysis_file=seg_file
            )
            sys.stdout.flush()
            print(seg_file+"-SegDone")
            sys.stdout.flush()


    h5_files = yaml_data.get_file_paths('h5')
    if h5_files is not None:
        logging.info('Loading H5 data')
        for hdf_paths in h5_files:
            segs_loader.load_file(
                analysis_file=hdf_paths['base'],
                subpath=hdf_paths['segs']
            )


def load_metrics_data(args, yaml_data):
    logging.info("")
    logging.info("")
    logging.info("==================")
    logging.info("LOADING METRIC DATA")
    logging.info("==================")
    index_name = yaml_data.get_index_name(dashboard_type, "qc")

    metrics_loader = MetricsLoader(
        es_doc_type=index_name,
        es_index=index_name,
        es_host=args.host,
        es_port=args.port
    )

    metric_files = yaml_data.get_file_paths('metrics')
    h5_files = yaml_data.get_file_paths('h5')

    if metric_files is not None:
        if metrics_loader.es_tools.exists_index():
            logging.info('Metric data for analysis already exists - will delete old index')
            metrics_loader.es_tools.delete_index()

        for metric_file in metric_files:
            metrics_loader.load_file(
                analysis_file=metric_file
            )


    if h5_files is not None:
        logging.info('Loading H5 data')
        for hdf_paths in h5_files:
            try:
                metrics_loader.load_file(
                    analysis_file=hdf_paths['base'],
                    subpath=hdf_paths['metrics']
                )
            except KeyError:
                pass


def load_bins_data(args, yaml_data):
    logging.info("")
    logging.info("")
    logging.info("==================")
    logging.info("LOADING BINS DATA")
    logging.info("==================")

    if yaml_data.has_type('skip_bins'):
        logging.info('Skipping bin load')
        return

    index_name = yaml_data.get_index_name(dashboard_type, "bins")

    bins_loader = BinsLoader(
        es_doc_type=index_name,
        es_index=index_name,
        es_host=args.host,
        es_port=args.port
    )

    bin_files = yaml_data.get_file_paths('bins')
    h5_files = yaml_data.get_file_paths('h5')


    if bins_loader.es_tools.exists_index():
        logging.info('Bin data for analysis already exists - will delete old index')
        bins_loader.es_tools.delete_index()


    has_bin_data = False

    if bin_files is not None:
        logging.info('Loading CSV tables')
        for bin_file in bin_files:
            bins_loader.load_file(
                analysis_file=bin_file
            )
        has_bin_data = True


    if h5_files is not None:
        logging.info('Loading H5 data')
        try:
            for hdf_paths in h5_files:
                bins_loader.load_file(
                    analysis_file=hdf_paths['base'],
                    subpath=hdf_paths['bins']
                )
            has_bin_data = True
        except KeyError:
            pass

    if has_bin_data:
        logging.info("")
        logging.info("")
        logging.info("==================")
        logging.info("NORMALIZING SEGMENT DATA TO MODE")
        logging.info("==================")
        norm_segs_index = yaml_data.get_index_name(dashboard_type, "nsegs")
        norm_segs_loader = SegsLoader(
            es_doc_type=norm_segs_index,
            es_index=norm_segs_index,
            es_host=args.host,
            es_port=args.port
        )

        normalize_segs(bins_loader, norm_segs_loader)


def run_preprocessing(args, yaml_data):
    logging.info("")
    logging.info("")
    logging.info("==================")
    logging.info("RUNNING PREPROCESSOR")
    logging.info("==================")

    if args.preprocessing is False:
        logging.info('Skipping preprocessing')
        return

    file_path = yaml_data.get_file_paths("tree")
    preprocessor = Preprocessor(
        newick_file=file_path,
        matching_required=args.match_id
    )

    preprocessor.preprocess()


def get_args():
    '''
    Argument parser
    '''
    parser = argparse.ArgumentParser(
        description=('Creates an index in Elasticsearch called published_dashboards_index, ' +
                     'and loads it with the data contained in the infile.')
    )
    required_arguments = parser.add_argument_group("required arguments")
    parser.add_argument(
        '-y',
        '--yaml_file',
        dest='yaml_file',
        action='store',
        help='Configuration file in Yaml format',
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
    parser.add_argument(
        '-pp',
        '--preprocessing',
        dest='preprocessing',
        action='store_true',
        help='Specifies whether preprocessing is required.',
        default=False)
    parser.add_argument(
        '-m',
        '--match-id',
        dest='match_id',
        action='store_true',
        help='Specifies whether preprocessing should run the match_id operation.',
        default=False)
    return parser.parse_args()

def main():
    args = get_args()
    _set_logger_config(args.verbosity)
    yaml_data = YamlData(args.yaml_file)
    run_preprocessing(args, yaml_data)
    load_tree_data(args, yaml_data)

    load_segs_data(args, yaml_data)
    load_metrics_data(args, yaml_data)
    load_bins_data(args, yaml_data)
    load_analysis_entry(args, yaml_data)

    sys.stdout.flush()
    print("DONE")
    sys.stdout.flush()

if __name__ == '__main__':
    main()
