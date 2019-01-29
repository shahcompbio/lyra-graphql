import sys
from common.tree_loader import TreeLoader



def main():
    data_type = sys.argv[1]

    if data_type == "tree":
        tree_loader = TreeLoader()
        file_path = sys.argv[2]
        json_data = tree_loader.load_file_as_json(analysis_file=file_path)

        print(json_data)
        sys.stdout.flush()



if __name__ == '__main__':
    main()