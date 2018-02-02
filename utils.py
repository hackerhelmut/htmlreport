#!/usr/bin/python
# vim: set fileencoding=utf-8
"""
Date time helper for the texstats
"""
from datetime import datetime
#import dateutil.parser

def now():
    """Return YYYY-MM-DDTXX:YY... string of the current date"""
    return datetime.now().isoformat()

#def parse_date(date_str):
#    """Parse iso date string"""
#    return dateutil.parser.parse(date_str)
