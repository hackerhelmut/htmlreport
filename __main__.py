#!/usr/bin/python
# vim: set fileencoding=utf-8
"""
Store daily statistics to generat fancy html page
"""

import yaml
from datastore import DataStore
from htmlgen import HTMLGen

def args_parser():
    """Configure argsparser for texstats"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Aggregate tex document statistics over time.')
    parser.add_argument(
        'tex_file', metavar='TEX_FILE',
        help='Main tex file to extract data from')
    parser.add_argument(
        '--config', dest='config',
        help='Datastore to agregate statistics over time. Defaults to ./.texstats.yaml')
    parser.add_argument(
        '--store', dest='store',
        help='Datastore to agregate statistics over time. Defaults to ~/.texstats-<MAIN_FILE>')
    parser.add_argument(
        '--noscan', dest='scan', action='store_false', default=True,
        help='Do not update datastore')
    parser.add_argument(
        '--query', dest='query',
        help='Query value')
    parser.add_argument(
        '--html', dest='html', action='store_true', default=False,
        help='export current statistics as html')

    return parser.parse_args()

def main():
    """Main function"""
    args = args_parser()
    with DataStore(args) as store:
        self.load_plugins()
        #self.run_plugins('options', parser)
        self.run_plugins('configure', args)
        data = self.run_plugins('execute')
        if store.query('$.args.scan'):
            store.insert(data)
        query = store.query('$.args.query')
        if query:
            print yaml.dump(store.query(query))

if __name__ == '__main__':
    main()
