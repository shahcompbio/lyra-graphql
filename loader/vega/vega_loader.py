#!/usr/bin/env python
import sys
sys.path.append('/lyra-graphql/loader')
import json
from common.tree_loader import TreeLoader


def main():
    data_type = sys.argv[1]
    file_name = sys.argv[3]

    if data_type == "tree":
        tree_loader = TreeLoader()
        file_path = sys.argv[2]
        json_data = tree_loader.load_file_as_json(analysis_file=file_path)

        with open('./mount/'+file_name, 'w') as outfile:
            json.dump(json_data, outfile)
        print("complete")
        sys.stdout.flush()

if __name__ == '__main__':
    main()
