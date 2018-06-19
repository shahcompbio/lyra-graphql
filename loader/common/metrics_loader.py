'''
Parser/Indexer for metric data in csv format

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
from utils.analysis_loader import AnalysisLoader


class MetricsLoader(AnalysisLoader):

    ''' Class TreeLoader '''

    __index_buffer__ = []
    __field_mapping__ = {
    }

    __field_types__ = {
        "cell_id": "str",
        "state_mode": "int"
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
        super(MetricsLoader, self).__init__(
            es_doc_type=es_doc_type,
            es_index=es_index,
            es_host=es_host,
            es_port=es_port,
            use_ssl=use_ssl,
            http_auth=http_auth,
            timeout=timeout)

    def load_file(self, analysis_file=None):
        if not self.es_tools.exists_index():
            self.create_index()

        self.disable_index_refresh()
        self._get_csv_dialect(analysis_file)
        self._load_metrics_data(analysis_file)

        self.enable_index_refresh()

    def _get_csv_dialect(self, csv_file):
        '''
        Gets the CSV file format properties
        '''
        try:
            with open(csv_file) as csv_fh:
                sniffer = csv.Sniffer()
                self.__csv_dialect__ = sniffer.sniff(csv_fh.readline())
                self.__csv_dialect__.quoting = csv.QUOTE_NONE
        except IOError:
            logging.error('Unable to parse CSV file.')
            exit(1)

    def _load_metrics_data(self, analysis_file):
        with open(analysis_file) as csv_fh:
            csv_reader = csv.DictReader(csv_fh, dialect=self.__csv_dialect__)

            for csv_record in csv_reader:
                index_record = self._update_record_keys(csv_record)
                index_record = {
                    key: self._apply_type(index_record, key)
                    for key in self.__field_types__.keys()
                }

                self._buffer_record(index_record, False)

        # Submit any records remaining in the buffer for indexing
        self._buffer_record(None, True)



    def _update_record_keys(self, index_record):
        '''
        Renames index record attributes as specified in the
        '__field_mapping__' reference
        '''
        for key in self.__field_mapping__.keys():
            if self.__field_mapping__[key] in index_record.keys():
                index_record[key] = index_record[self.__field_mapping__[key]]
            try:
                del index_record[self.__field_mapping__[key]]
            except KeyError:
                pass

        return index_record


    def _apply_type(self, record, key):
        '''
        Attempts to apply the data type associated with this record attribute
        '''
        if self._is_empty_value(record, key):
            return None

        key_type = getattr(__builtin__, self.__field_types__[key])
        try:
            return key_type(re.sub(r'"', '', record[key]))
        except ValueError:
            # In some cases values in a column with expected integer values
            # seem to get stored as floats, i.e. '2.0', make sure the error
            # is not the result of such case
            return key_type(re.sub(r'\.0$', '', record[key]))

    def _is_empty_value(self, record, key):
        '''
        Checks if the record holds an empty value in the specified field
        '''
        try:
            return math.isnan(record[key])
        except TypeError:
            pass

        value = str(record[key]).lower()
        if value in ['na', 'nan', 'inf', '?'] and self.__field_types__[key] != 'str':
            return True

        return not value.strip()


    def _buffer_record(self, index_record, empty_buffer=False):
        '''
        Appends records to the buffer and submits them for indexing
        '''
        if isinstance(index_record, dict):
            index_cmd = self.get_index_cmd()
            self.__index_buffer__.append(index_cmd)
            self.__index_buffer__.append(index_record)

        if len(self.__index_buffer__) >= self.LOAD_FACTOR or empty_buffer:
            self.es_tools.submit_bulk_to_es(self.__index_buffer__)
            self.__index_buffer__ = []



def get_args():
    '''
    Argument parser
    '''
    parser = argparse.ArgumentParser(
        description=('Parses CSV metric data in metrics_file and loads it into Elasticsearch index')
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
        '-metrics',
        '--metrics_file',
        dest='metrics_file',
        action='store',
        help='Metrics data file',
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
    es_loader = MetricsLoader(
        es_doc_type=args.index,
        es_index=args.index,
        es_host=args.host,
        es_port=args.port)

    es_loader.load_file(analysis_file=args.metrics_file)




if __name__ == '__main__':
    main()
