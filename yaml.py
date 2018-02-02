#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Implements yaml loading and storring
"""
from __future__ import print_function
import sys
import types
import itertools
from ruamel import yaml
from ruamel import ordereddict
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml import scalarstring

FILE_PROPERTY = "file"
FILE_EXTENSION = ".yaml"

class Query(object):
    """Query object"""
    def __init__(self, query):
        """
        Store query string
        """
        self.query = query

    def __repr__(self):
        """
        Print string representation of the query
        """
        return "!query:"+self.query
    def get_query(self):
        """
        Return the query string
        """
        return self.query


def query_constructor(loader, node):
    """
    Convert node as scalar from loader to a Query object
    """
    value = loader.construct_scalar(node)
    return Query(value)
yaml.add_constructor(u'!query', query_constructor, yaml.RoundTripLoader)

def query_representer(dumper, data):
    """
    Convert Query object to a query string with tag
    """
    return dumper.represent_scalar(u'!query', data.query)
yaml.add_representer(Query, query_representer, yaml.RoundTripDumper)

class folded_str(unicode): pass

def folded_str_representer(dumper, data):
    """
    Converts all folded_str instances to strings folded in YAML with the > style
    """
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')
yaml.add_representer(folded_str, folded_str_representer, yaml.RoundTripDumper)

class literal_str(unicode): pass

def literal_str_representer(dumper, data):
    """
    Converts all literal_str instances to strings in YAML with the | style
    """
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
yaml.add_representer(literal_str, literal_str_representer, yaml.RoundTripDumper)


def load(filename):
    """Load a dict from a yaml file"""
    try:
        result = {}
        with open(filename, "r") as stream:
            result = yaml.load(stream.read(), Loader=yaml.RoundTripLoader)
    except yaml.reader.ReaderError as err:
        print("Error in file:", filename)
        print(err.message())
        sys.exit(1)
    except yaml.scanner.ScannerError as err:
        print("Error in file {filename} ".format(filename=filename), err)
        sys.exit(1)
    except yaml.parser.ParserError as err:
        print("Error in file {filename} ".format(filename=filename), err)
        sys.exit(1)
    return result

def load_all(filename):
    """Load a dict from a yaml file"""
    try:
        result = {}
        with open(filename, "r") as stream:
            result = yaml.load_all(stream.read(), Loader=yaml.RoundTripLoader)
    except yaml.reader.ReaderError as err:
        print("Error in file:", filename)
        print(err.message())
        sys.exit(1)
    except yaml.scanner.ScannerError as err:
        print("Error in file {filename} ".format(filename=stream.filename), err)
        sys.exit(1)
    except yaml.parser.ParserError as err:
        print("Error in file {filename} ".format(filename=filename), err)
        sys.exit(1)
    return result

def dump(obj):
    """Dump a dict as yaml into a string"""
    if isinstance(obj, types.GeneratorType):
        obj = tuple(obj)
    elif isinstance(obj, itertools.chain):
        obj = list(obj)
    return u"---\n"+yaml.dump(obj, Dumper=yaml.RoundTripDumper)

def dump_all(obj, **kw):
    """Dump a dict as yaml into a string"""
    if isinstance(obj, types.GeneratorType):
        obj = tuple(obj)
    elif isinstance(obj, itertools.chain):
        obj = list(obj)
    return yaml.dump_all(obj, Dumper=yaml.RoundTripDumper, **kw)


