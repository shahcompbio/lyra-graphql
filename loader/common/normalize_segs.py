import logging
import argparse
import sys
import os
import pandas as pd

from bins_loader import BinsLoader
from segs_loader import SegsLoader


def normalize_segs(bin_index, norm_segs_loader):
    mode_bins = _get_bin_modes(bin_index)
    mode_segs = _convert_to_segs(mode_bins)

    mode_bin_map = _get_bin_map(mode_bins)

    all_cell_segs = [] + mode_segs

    cell_ids = _get_cell_ids(bin_index)

    for cell_id in cell_ids:
        cell_segs = _get_cell_segs(bin_index, cell_id, mode_bin_map)
        all_cell_segs = all_cell_segs + cell_segs

    data_table = pd.DataFrame(all_cell_segs)
    data_table = data_table.loc[:, ['cell_id', 'chrom_number', 'start', 'end', 'state']]
    norm_segs_loader._load_segs_table(data_table)


def _convert_to_segs(bins):
    '''
    Assume sorted by increasing start
    '''
    segs = []
    currSeg = None

    for bin in bins:
        if currSeg is None:
            currSeg = bin

        elif bin['state'] == currSeg['state'] and bin['chrom_number'] == currSeg['chrom_number']:
            currSeg = {
                "cell_id": currSeg["cell_id"],
                "chrom_number": currSeg['chrom_number'],
                "state": currSeg['state'],
                "start": currSeg['start'],
                "end": bin['end']
            }

        else:
            segs = segs + [currSeg]
            currSeg = bin

    return segs + [currSeg]


'''
#################
FIND MODE OF BINS
#################
'''
def _get_bin_modes(bin_index):
    query = _bin_modes_query()

    results = bin_index.es_tools.raw_search(query)
    chromosomes = results['aggregations']['chromosomes']['buckets']

    bins = reduce((lambda bins, chrom: bins + _process_chrom_bucket(chrom)), chromosomes, [])

    return bins



def _bin_modes_query():
    return {
        "size": 0,
        "aggs": {
            "chromosomes": {
                "terms": {
                    "field": "chrom_number",
                    "size": 50
                },
                "aggs": {
                    "bins": {
                        "histogram": {
                            "field": "start",
                            "interval": 500000,
                            "offset": 1
                        },
                        "aggs": {
                            "state": {
                                    "terms": {
                                    "field": "state",
                                    "size": 1
                                }
                            }
                        }
                    }
                }
            }
        }
    }

def _process_chrom_bucket(chrom):
    chromosome = chrom['key']

    bins = [_process_bin_bucket(bin, chromosome) for bin in chrom['bins']['buckets']]
    return bins

def _process_bin_bucket(bin, chromosome):
    start = int(bin['key'])
    return {
        "cell_id": "all",
        "chrom_number": chromosome,
        "start": start,
        "end": int(start + 500000),
        "state": bin['state']['buckets'][0]['key']
    }

'''
#################
Converting bins to map
#################
'''

def _get_bin_map(bins):
    bin_map = {}

    for bin in bins:
        chrom_number = bin['chrom_number']
        start = bin['start']
        key = chrom_number + "_" + str(start)
        bin_map[key] = bin['state']

    return bin_map


'''
#################
Calculating diff of bins for each cell
#################
'''
def _get_cell_ids(bin_index):
    query = {
        "size": 0,
        "aggs": {
            "cell_ids": {
                "terms": {
                    "field": "cell_id",
                    "size": 100000
                }
            }
        }
    }

    results = bin_index.es_tools.raw_search(query)

    cell_ids = [bucket['key'] for bucket in results['aggregations']['cell_ids']['buckets']]

    return cell_ids

def _get_cell_segs(bin_index, cell_id, mode_bin_map):
    bins = _get_cell_bins(bin_index, cell_id)
    bins = [_diff_bin(bin, mode_bin_map) for bin in bins]

    segs = _convert_to_segs(bins)

    return segs


def _get_cell_bins(bin_index, cell_id):
    query = {
        "size": 50000,
        "query": {
            "bool": {
                "must": [{
                    "term": {
                        "cell_id": {
                            "value": cell_id
                        }
                    }
                }]
            }
        },
        "sort": [{
            "chrom_number": {
                "order": "asc"
            }
        }, {
            "start": {
                "order": "asc"
            }
        }]
    }

    results = bin_index.es_tools.raw_search(query)

    return [record["_source"] for record in results['hits']['hits']]

def _diff_bin(bin, mode_bin_map):
    chromosome = bin['chrom_number']
    start = bin['start']
    key = chromosome + "_" + str(start)
    bin['state'] = bin['state'] - mode_bin_map[key]

    return bin


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
        '-bi',
        '--bin_index',
        dest='bin_index',
        action='store',
        help='Name of index with bin data',
        type=str)
    parser.add_argument(
        '-si',
        '--segs_index',
        dest='segs_index',
        action='store',
        help='Name of index to load segment data in',
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
    bin_loader = BinsLoader(
        es_doc_type=args.bin_index,
        es_index=args.bin_index,
        es_host=args.host,
        es_port=args.port
    )

    segs_loader = SegsLoader(
        es_doc_type=args.segs_index,
        es_index=args.segs_index,
        es_host=args.host,
        es_port=args.port
    )
    normalize_segs(bin_loader, segs_loader)


if __name__ == '__main__':
    main()
