'''
Parser/Indexer for segment data in csv or h5 format

'''

import csv
import ast
import re
import copy
import logging
import argparse
import sys
import os
import math
import __builtin__
import networkx as nx
import pandas as pd
from utils.analysis_loader import AnalysisLoader

class SegsLoader(AnalysisLoader):

    ''' Class SegsLoader '''


    __field_mapping__ = {
        "median": "integer_median",
        "chr": "chrom_number"
    }


    def __init__(
            self,
            es_doc_type=None,
            es_index=None,
            es_host=None,
            es_port=None,
            use_ssl=False,
            http_auth=None,
            timeout=None):
        super(SegsLoader, self).__init__(
            es_doc_type=es_doc_type,
            es_index=es_index,
            es_host=es_host,
            es_port=es_port,
            use_ssl=use_ssl,
            http_auth=http_auth,
            timeout=timeout)


    def load_file(self, analysis_file=None, subpath=None):
        data = self._read_file(analysis_file, subpath)
        self._load_segs_table(data)

    def _read_file(self, file, subpath):
        if file.endswith('.csv'):
            return pd.read_csv(file)

        elif file.endswith('.h5'):
            hdf = pd.HDFStore(file, 'r')
            return hdf.get(subpath)


    def _update_columns(self, columns):
        '''
        Renames columns attributes as specified in the
        '__field_mapping__' reference
        '''
        return [self.__field_mapping__[key] if key in self.__field_mapping__.keys() else key for key in columns]


    def _load_segs_table(self, data):
        data.columns = self._update_columns(data.columns.values)
        data['chrom_number'] = data['chrom_number'].apply(_format_chrom_number)

        if not self.es_tools.exists_index():
            self.create_index()

        self.disable_index_refresh()
        self.es_tools.submit_df_to_es(data)
        self.enable_index_refresh()


def _format_chrom_number(chrom_number):
    '''
    Formats the index record chrom_number field
    '''
    convert_chrom = {"23": 'X', "24": 'Y'}

    if str(chrom_number) in convert_chrom.keys():
        return convert_chrom[str(chrom_number)]

    if re.match(r'^\d{1,2}$', chrom_number):
        return chrom_number.zfill(2)

    return chrom_number.upper()



def get_args():
    '''
    Argument parser
    '''
    parser = argparse.ArgumentParser(
        description=('Creates an index in Elasticsearch called for segments and loads appropriate CSV file')
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
        '-segs',
        '--segs_file',
        dest='segs_file',
        action='store',
        help='Segs data file',
        type=str)
    parser.add_argument(
        '-sub',
        '--subpath',
        dest='subpath',
        action='store',
        help='Path to segs file within h5',
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
    es_loader = SegsLoader(
        es_doc_type=args.index,
        es_index=args.index,
        es_host=args.host,
        es_port=args.port)

    es_loader.load_file(analysis_file=args.segs_file, subpath=args.subpath)


if __name__ == '__main__':
    main()
