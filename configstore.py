#!/usr/bin/python
# vim: set fileencoding=utf-8
"""
Simple YAML based configstore for texstats
"""
import os
import yaml
import types
import itertools
from objectpath import Tree

class ConfigStore(object):
    """YAML based datastore implementation"""
    template_path = None
    def __init__(self, args):
        """
        Prepare for usage. Filename as argumten
        Open and read datastore
        """
        if 'config' in args and args.config:
            self.store = args.config
        else:
            self.store = '.texstats.yaml'
        self.data = {}

        if not os.path.exists(self.store):
            self.data = {}
        else:
            print 'Config:', self.store
            self.data = yaml.load(self.store)

        self.tree = self.init_tree(self.data)

    """Query the current database with ObjectPath"""
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

    def init_tree(self, data):
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
        tree = Tree(data, cfg={
            "debug": False,
            "object_getter": self.query_getter
        })
        tree.register_function("first", first_funct)
        tree.register_function("update", update_funct)
        tree.register_function("keys", keys_funct)
        tree.register_function("values", values_funct)
        return tree

    def query(self, querystr, **kw):
        """
        Get element from config
        """
        full_query = querystr.format(**kw)
        res = self.tree.execute(full_query)
        return self.query_getter(res, None)
