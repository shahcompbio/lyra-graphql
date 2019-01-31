import yaml
import logging
import traceback
import argparse
import os
import sys
import dashboards



class YamlData(object):
    def __init__(self, yaml_file_path):
        self.yaml_path = yaml_file_path
        yaml_data = self.parse_yaml_file(yaml_file_path)
        self.yaml_data = yaml_data

    def parse_yaml_file(self, yaml_file):
        '''
        returns a dictionary with parsed data from a yaml input file and
        extracts and adds the run id from the file name
        '''
        if not os.path.isfile(yaml_file):
            return

        input_file = open(yaml_file, 'r')
        file_data = '\n'.join(input_file.readlines())
        input_file.close()

        try:
            yaml_data = yaml.load(file_data)
        except ScannerError:
            logging.error("Error parsing yaml file %s.", yaml_file)
            return {}

        if not isinstance(yaml_data, dict):
            return

        return yaml_data


    def has_type(self, key):
        return key in self.yaml_data['files']


    def get_index_name(self, dashboard, type):
        dashboard_code = dashboards.DASHBOARDS[dashboard].lower()
        base_index_name = self.yaml_data['analysis_id'].lower()

        return dashboard_code + "_" + base_index_name + "_" + type.lower()


    def get_file_paths(self, type):
        files = self.yaml_data['files']

        try:
            return files[type.lower()]
        except KeyError:
            logging.info("No file with key %s.", type)
            return None


    def get_analysis_entry(self, dashboard):

        record = {
            'analysis_id': self.yaml_data['analysis_id'],
            'title': self.yaml_data['title'],
            'jira_id': self.yaml_data['jira_id'],
            'library_ids': [library_id for library_id in self.yaml_data['library_ids']],
            'sample_ids': [sample_id for sample_id in self.yaml_data['sample_ids']],
            'project': self.yaml_data['project'],
            'description': self.yaml_data['description'],
            'dashboard': dashboard
        }

        return record
