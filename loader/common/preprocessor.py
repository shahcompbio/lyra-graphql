import re

class Preprocessor(object):
    '''
    Runs preprocessing operations (if required)
    '''
    def __init__(self, newick_file, matching_required=False):
        self.newick_file = newick_file
        self.matching_required = matching_required

    def trim_prefixes_and_add_root(self):
        with open(self.newick_file, 'r+') as newick_file:
            newick_string = newick_file.read().replace('\n', '')

            newick_string = re.sub(';', 'root;', newick_string)
            newick_string = newick_string.replace('cell_', '')

            newick_file.seek(0)
            newick_file.write(newick_string)
            newick_file.truncate()

    def match_ids(self):
        with open(self.newick_file, 'r+') as newick_file:
            newick_string = newick_file.read()

            newick_string = re.sub('(SA[0-9]+)[a-zA-Z]+', r'\1', newick_string)

            newick_file.seek(0)
            newick_file.write(newick_string)
            newick_file.truncate()

    def preprocess(self):
        self.trim_prefixes_and_add_root()

        if self.matching_required:
            self.match_ids()
