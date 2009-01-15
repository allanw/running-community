# -*- coding: utf-8 -*-
_FORBIDDEN_LAZY_FUNCS = ('__init__', '__new__', '__getattr__', '__hasattr__',
                         '__setattr__', '__dict__')

def resolve_lazy(func):
    def resolver(self, *args, **kwargs):
        if func.__name__ in ('__getattr__', '__hasattr__', '__setattr__') and \
                (args[0].startswith('_LaZy_') or self._LaZy_initializing):
            if func.__name__ == '__getattr__':
                try:
                    return self.__dict__[args[0]]
                except KeyError:
                    raise AttributeError(args[0])
            elif func.__name__ == '__hasattr__':
                return args[0] in self.__dict__[args[0]]
            elif func.__name__ == '__setattr__':
                self.__dict__[args[0]] = args[1]
                return
        if self._LaZy_func:
            self._LaZy_delegate = self._LaZy_func()
            self._LaZy_func = None
        return func(self, *args, **kwargs)
    return resolver

class LazyObject(object):
    def __init__(self, func, *delegates):
        self._LaZy_initializing = True
        self._LaZy_func = func
        self._LaZy_delegate = None
        for delegate in delegates:
            for key, value in delegate.__dict__.items():
                if key.startswith('__') and key.endswith('__') and \
                        key not in _FORBIDDEN_LAZY_FUNCS:
                    setattr(self, key, resolve_lazy(value))
        self._LaZy_initializing = False

    @resolve_lazy
    def __getattr__(self, attr):
        return getattr(self._LaZy_delegate, attr)

    @resolve_lazy
    def __hasattr__(self, attr):
        return hasattr(self._LaZy_delegate, attr)

    @resolve_lazy
    def __setattr__(self, attr, value):
        return setattr(self._LaZy_delegate, attr, value)

def getattr_by_path(obj, attr, *default):
    """Like getattr(), but can go down a hierarchy like 'attr.subattr'"""
    value = obj
    for part in attr.split('.'):
        if not hasattr(value, part) and len(default):
            return default[0]
        value = getattr(value, part)
        if callable(value):
            value = value()
    return value

def subdict(data, *attrs):
    """Returns a subset of the keys of a dictionary."""
    result = {}
    result.update([(key, data[key]) for key in attrs])
    return result

def equal_lists(left, right):
    """
    Compares two lists and returs True if they contain the same elements, but
    doesn't require that they have the same order.
    """
    right = list(right)
    if len(left) != len(right):
        return False
    for item in left:
        if item in right:
            del right[right.index(item)]
        else:
            return False
    return True

def object_list_to_table(headings, dict_list):
    """
    Converts objects to table-style list of rows with heading:

    Example:
    x.a = 1
    x.b = 2
    x.c = 3
    y.a = 11
    y.b = 12
    y.c = 13
    object_list_to_table(('a', 'b', 'c'), [x, y])
    results in the following (dict keys reordered for better readability):
    [
        ('a', 'b', 'c'),
        (1, 2, 3),
        (11, 12, 13),
    ]
    """
    return [headings] + [tuple([getattr_by_path(row, heading, None)
                                for heading in headings])
                         for row in dict_list]

def dict_list_to_table(headings, dict_list):
    """
    Converts dict to table-style list of rows with heading:

    Example:
    dict_list_to_table(('a', 'b', 'c'),
        [{'a': 1, 'b': 2, 'c': 3}, {'a': 11, 'b': 12, 'c': 13}])
    results in the following (dict keys reordered for better readability):
    [
        ('a', 'b', 'c'),
        (1, 2, 3),
        (11, 12, 13),
    ]
    """
    return [headings] + [tuple([row[heading] for heading in headings])
                         for row in dict_list]
