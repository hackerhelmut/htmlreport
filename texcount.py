#!/usr/bin/python
# vim: set fileencoding=utf-8
"""
texcount parser and preparation for texstats
"""
import sys
from pyparsing import ParserElement, Word, nums
from pyparsing import restOfLine, OneOrMore, Suppress
from pyparsing import SkipTo, Group, Dict
from pyparsing import LineEnd, Optional, StringEnd
from utils import now
from plugin import register, Plugin

ParserElement.setDefaultWhitespaceChars(' \t')

# Control characters
EOL = LineEnd().suppress()
SEP, PLUS, DIV, BO, BC = map(Suppress, ':+/()')

# Keywords
ENDKEY = Suppress('Subcounts')

@register('texcount')
class Texcount(Plugin):
    """
    Texcount input class
    """
    # Keywords to dict names
    HEADERTYPE = {
        'Included file': 'file',
        'Chapter': 'chapter',
        'Section': 'section',
        'Subsection': 'subsection',
        'Subsubsection': 'subsubsection',
    }
    KEYWORDS = {
        'Included file': 'file',
        'Encoding': 'encoding',
        'Words in text': 'text',
        'Words in headers': 'headers',
        'Words outside text (captions, etc.)': 'captions',
        'Number of headers': 'headers_count',
        'Number of floats/tables/figures': 'floats_count',
        'Number of math inlines': 'inlines_count',
        'Number of math displayed': 'displayed',
        'File(s) total': 'sum',
        'Files': 'file_count',
        'File': 'file',
    }
    def __init__(self, store):
        """Return a parser of a texcount output parser"""
        self.store = store

        # Literals
        value = restOfLine.setParseAction(lambda s, l, t: [t[0].strip()])
        number = Word(nums).setParseAction(lambda s, l, t: [int(t[0])])
        blockheader = SkipTo(SEP).setParseAction(lambda s, l, t: [self.HEADERTYPE[t[0].strip()]])
        keyword = SkipTo(SEP).setParseAction(lambda s, l, t: [self.KEYWORDS[t[0].strip()]])

        # Statements
        number_line = Group(
            number('text') + PLUS +
            number('headers') + PLUS +
            number('captions') +
            BO + (
                number('num_headers') + DIV +
                number('num_floats') + DIV +
                number('num_inlines') + DIV +
                number('num_displayed')
            ) + BC + blockheader('type') + SEP +
            value('name') +
            EOL
        )

        keyval_line = Group(~EOL + ~ENDKEY + keyword + SEP + value + EOL)
        numbers = ENDKEY + SEP + EOL + restOfLine.suppress() + EOL + OneOrMore(number_line)
        block = Group(
            Dict(OneOrMore(keyval_line))('fields') +
            Optional(numbers('numbers'))
        ) + (EOL | StringEnd())
        # Document
        self.parse = OneOrMore(block)

    def prepare(self, data):
        """Reorder output segments to correspond by files and sections from the root section"""
        root = None
        files = {}
        for item in data:
            if 'sum' in item.fields.keys():
                root = item
            if 'file' in item.fields.keys():
                files[item.fields.file] = item

        root.files = []
        root.sections = []
        for item in root.numbers:
            name = item.name
            filedata = files[name]
            root.files.append(filedata)
            if 'numbers' in filedata.keys():
                for section in filedata.numbers:
                    root.sections.append(section)
        return root

    def format(self, root):
        """Prepare output format. All data is be prepared as a dict"""
        data = {}
        for key in ['file_count', 'text', 'headers_count', 'floats_count']:
            data[key] = int(root.fields[key])
        data['sections'] = []
        data['section_count'] = len(root.sections)
        for section in root.sections:
            sec_out = {}
            for key in ['text', 'num_headers', 'captions', 'type', 'name']:
                sec_out[key] = section[key]
            data['sections'].append(sec_out)
        data['files'] = []
        for filedata in root.numbers:
            file_out = {}
            for key in ['text', 'num_headers', 'captions', 'type', 'name']:
                file_out[key] = filedata[key]
            data['files'].append(file_out)
        return data

    def options(self, parser):
        parser.add_argument(
            'tex_file', metavar='TEX_FILE',
            help='Main tex file to extract data from')

    def configure(self, args):
        self.pathname = args.tex_file
        

    def execute(self):
        """Execute texcount perl command"""
        import os
        import subprocess
        text = ""
        if self.store.query('$.args.scan'):
            try:
                dirname = os.path.dirname(self.pathname)
                filename = os.path.basename(self.pathname)
                text = subprocess.check_output(['texcount', '-inc', filename], cwd=dirname)
            except OSError:
                print ("Cannot find or execute 'texcount'. ",
                       "Please ensure that the command is in the current path")
                sys.exit(3)

            ast = self.parse.parseString(text)
            data = self.format(self.prepare(ast))
            return data
        else:
            return {}
