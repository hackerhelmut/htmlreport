#!/usr/bin/python
# vim: set fileencoding=utf-8
"""
Uses the datastore to generate a HTML page
"""

import os
import shutil
import template
from plugin import register, Plugin

@register('htmlgen')
class HTMLGen(Plugin):
    """
    Texstats jinja2 html generator
    """
    templatedir = os.path.dirname(__file__)
    template = os.path.join(os.path.dirname(__file__), 'template.html')
    def __init__(self, store):
        """
        Set store variable and prepare template
        """
        template.init(store)
        self.store = store
        self.template = template.Template(filename=self.template)

    def options(self, parser):
        parser.add_argument(
            '--html', dest='html', action='store_true', default=False,
            help='export current statistics as html')

    def configure(self):
        pass

    def execute(self):
        """
        Fill template with data
        """
        if self.store.query('$.args.html'):
            html_conf = {}
            module_conf = self.store.query('first($.config..*[@.name is "htmlgen"])')
            html_conf.update(**module_conf)
            html_conf.update(self.store.store)
            outdir = self.store.query('first($.config..*[@.name is "htmlgen"]).outdir')
            if not os.path.exists(outdir):
                shutil.copytree(
                    os.path.join(self.templatedir, 'assets'),
                    os.path.join(outdir, 'assets'),
                    symlinks=True
                )
                shutil.copy(os.path.join(self.templatedir, 'moment.min.js'), os.path.join(outdir, 'assets', 'js', 'moment.min.js'))
            pdf_in = self.store.query('$.config.pdf or slice($.config.main, [0,-4])+".pdf"')
            pdf_out = os.path.join(outdir, 'index.pdf')
            shutil.copy(pdf_in, pdf_out)
            with open(os.path.join(outdir, 'index.html'), 'w') as stream:
                stream.write(self.template.format(**html_conf).encode('UTF-8'))
