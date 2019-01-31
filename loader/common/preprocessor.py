import re

class Preprocessor(object):
    '''
    Runs preprocessing operations (if required)
    '''
    def __init__(self, newick_file, matching_required=False):
        self.newick_file = newick_file
        self.matching_required = matching_required

    def trim_prefixes(self, newick_string):
        newick_string = newick_string.replace('cell_', '')
        return newick_string

    def add_root(self, newick_string):
        if re.search('root;', newick_string) is None:
            newick_string = re.sub(';', 'root;', newick_string)
        return newick_string

    def match_ids(self, newick_string):
        newick_string = re.sub('(SA[0-9]+)[a-z]', r'\1', newick_string)
        return newick_string

    def preprocess(self):
        with open(self.newick_file, 'r+') as newick_file:
            newick_string = newick_file.read().replace('\n', '')

            newick_string = self.trim_prefixes(newick_string)
            newick_string = self.add_root(newick_string)

            if self.matching_required:
                newick_string = self.match_ids(newick_string)

            newick_file.seek(0)
            newick_file.write(newick_string)
            newick_file.truncate()
