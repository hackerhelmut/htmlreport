#!/usr/bin/python
# vim: set fileencoding=utf-8
"""
Simple YAML based datastore for texstats
"""
from __future__ import print_function
import os
import sys
import yaml
import types
import itertools
from objectpath import Tree
from os.path import expanduser, basename

def first_funct(*k):
    """Returns the first result"""
    if len(k) == 1 and isinstance(k[0], (tuple, list)):
        k = k[0]
    for obj in k:
        if isinstance(obj, types.GeneratorType):
            obj = tuple(obj)
            if len(obj) == 1:
                obj = obj[0]
            elif not len(obj):
                obj = None
        elif isinstance(obj, itertools.chain):
            obj = list(obj)
            if len(obj) == 1:
                obj = obj[0]
            elif not len(obj):
                obj = None
        if obj != None:
            return obj
    return None

def update_funct(*k):
    """Allow dict.update in a query"""
    result = {}
    if isinstance(result, dict):
        for extra in k:
            if isinstance(extra, dict):
                result.update(extra)
    return result

def keys_funct(dictionary):
    """Allow dict.keys in a query"""
    if isinstance(dictionary, dict):
        return dictionary.keys()
    return dictionary

def values_funct(dictionary):
    """Allow dict.values in a query"""
    if isinstance(dictionary, dict):
        return dictionary.values()
    return dictionary

class DataStore(object):
    """YAML based datastore implementation"""
    def __init__(self, args):
        """Prepare for usage. Filename as argumten"""
        self.plugin = {}
        self.store = dict(
            data=[],
            config=dict(
                name=os.path.basename(args.main_file),
                datastore=args.store or expanduser(
                    '~/.texstats-{}'.format(basename(args.main_file))),
                configfile=args.config or '.texstats.yaml',
            ),
            args=vars(args)
        )
        if not os.path.exists(self.store['config']['configfile']):
            print("Please provide a valid configuration (default: .texstats.yaml)")
            sys.exit(1)

        self.store['config'].update(yaml.load(self.store['config']['configfile']))

        self.modified = False
        self.tree = Tree(self.store, cfg={
            "debug": False,
            "object_getter": self.query_getter
        })
        self.tree.register_function("first", first_funct)
        self.tree.register_function("update", update_funct)
        self.tree.register_function("keys", keys_funct)
        self.tree.register_function("values", values_funct)

    def query_getter(self, obj, attr):
        """Extended object getter to allow lazy recursive query resolving"""
        if isinstance(obj, types.GeneratorType):
            obj = tuple(obj)
        elif isinstance(obj, itertools.chain):
            obj = list(obj)
        if isinstance(obj, yaml.Query):
            res = self.query(obj.query, **kw)
            if attr:
                return res.get(attr)
            else:
                return res
        elif isinstance(obj, yaml.CommentedMap):
            res = obj.get(attr)
        try:
            if attr:
                return obj.__getattribute__(attr)
            else:
                return obj
        except AttributeError:
            return obj

    def __enter__(self):
        """The class is ment to be used as with guard"""
        self.open()
        return self

    def __exit__(self, typename, value, traceback):
        self.close()

    def open(self):
        """Open and read datastore"""
        storefile=expanduser(self.store['config']['datastore'])
        if not os.path.exists(storefile):
            return

        self.store['data'] = list(yaml.load_all(storefile))

    def close(self, save=True):
        """Close and write datastore"""
        if save and self.modified:
            with open(expanduser(self.store['config']['datastore']), 'w') as stream:
                stream.write(yaml.dump_all(
                    self.store['data'],
                    explicit_start=True,
                    default_flow_style=False,
                    encoding='utf-8'
                ))
                self.modified = False

    def insert(self, dataset):
        """Insert dataset into datastore."""
        self.store['data'].append(dataset)
        sorted(self.store['data'], key=lambda x: x['date'])
        self.modified = True

    def query(self, querystr, **kw):
        """
        Get element from config
        """
        full_query = querystr.format(**kw)
        res = self.tree.execute(full_query)
        obj = self.query_getter(res, None)
        return obj

    def load_plugins(self):
        import importlib
        from plugin import REGISTRY
        for path in reversed(self.store['config']['searchpath']):
            sys.path.insert(0, path)
        # match=re.findall(ex, txt, re.U|re.M)
        # from pylatexenc.latex2text import LatexNodes2Text
        # tex = LatexNodes2Text()
        # [tex.latex_to_text(m) for m in match]
        for plugin in self.query('$.config.plugins..*.name'):
            mod = importlib.import_module(plugin)
            self.plugin[plugin] = REGISTRY[plugin](self)


    def run_plugins(self, function='execute', *k, **kw):
        result = {}
        result['date'] = now()
        for plugin in self.store['config'].plugins:
            plugin = self.plugin[plugin.name]
            funct = getattr(plugin, function, None)
            if callable(funct):
                out = funct(*k, **kw)
                if out:
                    result[plugin] = out

