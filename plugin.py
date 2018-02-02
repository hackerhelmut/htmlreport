"""
This file contains the main plugin system for texstats
"""
REGISTRY = {}
def register(name):
    """
    Register Plugin class
    >>> @register('name')
    >>> class Foo(Plugin):
    """
    def func(cls):
        """
        See register
        """
        REGISTRY[name] = cls()
        return cls
    return func

class Plugin(object):
    """
    Plugin base class
    """
    def options(self, parser):
        """
        Define comand line arguments in parser
        """
        pass

    def configure(self, args):
        """
        Store comand line arguments for execution
        """
        pass

    def execute(self):
        """
        Execute Plugin code
        """
        pass
