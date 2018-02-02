#!/usr/bin/env python2.7
# vim : set fileencoding=utf-8 expandtab noai ts=4 sw=4 filetype=python :
"""
embeddedfactor GmbH 2015
Connects the jinja2 template engine
"""
from __future__ import print_function
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateSyntaxError
import os
import sys
import yaml
from ruamel import yaml as ryaml

FILTERS = {} # env['template']['filters']
LOADER = None
ENVIRONMENT = None
query = None
datastore = None

def init(datastore_):
    """Init template functionality"""
    global LOADER, ENVIRONMENT, query, datastore
    datastore = datastore_
    query = datastore.query
    LOADER = FileSystemLoader(datastore.store['config'].get('template_path', os.path.dirname(__file__)))
    ENVIRONMENT = Environment(loader=LOADER, line_statement_prefix='#%', line_comment_prefix='##')
    #FILTERS.update(ENVIRONMENT.filters)
    ENVIRONMENT.filters = FILTERS
    #env["template"].update({
    #    "loader": LOADER,
    #    "env": ENVIRONMENT,
    #})

def jinja2Split(string, delimer=' '):
    return string.split(delimer)
FILTERS['split'] = jinja2Split

def jinja2json(obj):
    import json
    return json.dumps(obj, indent=2)

FILTERS['json'] = jinja2json

def jinja2resolve(obj, **defaults):
    """Takes a dict sructure and resolves all queries"""
    try:
        result = None
        if isinstance(obj, yaml.Query):
            result = query(obj.query, **defaults)
        elif isinstance(obj, list):
            result = []
            for item in obj:
                result.append(jinja2resolve(item, **defaults))
        elif isinstance(obj, dict):
            result = {}
            for key, item in obj.items():
                result[key] = jinja2resolve(item, **defaults)
        elif isinstance(obj, Template):
            result = obj.format(**defaults)
        elif isinstance(obj, (str, unicode)):
            result = obj.format(**defaults)
        else:
            result = obj
        return result
    except KeyError as err:
        print("################################################################")
        print("The Key {} was not found in the dict. The following keys are available:".format(err.message))
        print(", ".join(defaults.keys()))
        print("")
        print("For more information run in debug mode (-d)")
        #if env.debug:
        #    import traceback
        #    traceback.print_stack()
        #    traceback.print_exc()
        sys.exit(1)

FILTERS['resolve'] = jinja2resolve

class Template(object):
    """Template object"""
    def __init__(self, template=None, filename=None):
        """
        Store query string
        """
        self.template = template
        self.filename = filename or ""
        if self.filename and not self.template:
            try:
                with open(self.filename, 'r') as filehandle:
                    self.template = filehandle.read().decode('UTF-8')
            except IOError as err:
                print("An IOError occured", err)
                sys.exit(1)

    def __repr__(self):
        """
        Print string representation of the template
        """
        return "!template "+self.template
    def get_template(self):
        """
        Return the template string
        """
        return self.template
    def format(self, *k, **kw):
        """
        Returns the evaluated templates with the given parameters.
        """
        if len(k) == 1 and isinstance(k[0], dict):
            kw.update(k[0])
        def jinja2Query(querystr, **query_kw):
            newkw = {}
            newkw.update(kw)
            newkw.update(query_kw)
            return query(querystr, **newkw)
        def isdict(name):
            return isinstance(name, dict)
        kw['query'] = jinja2Query
        kw['isdict'] = isdict
        kw.update(FILTERS)
        try:
            template = ENVIRONMENT.from_string(self.template)
            template.filename = self.filename
            return template.render(**kw)
        except TemplateSyntaxError as err:
            print("An rendering error occured {}:{}".format(
                self.filename, err.lineno), err)
            sys.exit(1)

def template_f(template=None, filename=None):
    """Create templates in a template"""
    return Template(template, filename)
FILTERS['template'] = template_f

def template_constructor(loader, node):
    """
    Convert node as scalar from loader to a Template object
    """
    value = loader.construct_scalar(node)
    if isinstance(value, dict):
        return Template(**value)
    else:
        return Template(value)
ryaml.add_constructor(u'!template', template_constructor, ryaml.RoundTripLoader)

def template_representer(dumper, data):
    """
    Convert Template object to a query string with tag
    """
    return dumper.represent_scalar(u'!template', data.template)
ryaml.add_representer(Template, template_representer, ryaml.RoundTripDumper)


