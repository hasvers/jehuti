from collections import *
from copy import *
from functools import total_ordering

# TOOL CLASSES
class sparse(dict):
    def __init__(self, default=0):
        dict.__init__(self)
        self.default = default
    def __missing__(self, key):
        return self.default

class sparsemat(dict):
    def __init__(self, default):
        dict.__init__(self)
        self.dummy=sparsedummy(default, self)

    def __missing__(self, key):
        self.dummy.miskey=key
        return self.dummy

class sparsedummy(MutableMapping):
    def __init__(self, default=0, parent=None):
        self.default=default
        self.parent=parent
        self.miskey=None
    def __getitem__(self, key):
        return self.default
    def __setitem__(self, key, value):
        newrow=sparse(self.default)
        newrow[key] = value
        self.parent[self.miskey]=newrow
    def __delitem__(self, key):
        return False
    def __iter__(self):
        return iter([])
    def __len__(self):
        return 0

class listdict(dict):
    def __missing__(self, key):
        self[key]=[]
        return self[key]


class typedict(dict):
    def __init__(self,typ=None):
        dict.__init__(self)
        if typ :
            self.typ=typ
        else:
            return {}

    def __setitem__(self, key, value):
        if isinstance(key,self.typ):
            dict.__setitem__(self,key,value)
        else :
            raise TypeError( "Wrong type in type dict of type "+ str(self.typ))
    def __getitem__(self, key):
        return dict.__getitem__(self,key)
    def __delitem__(self, key):
        return dict.__delitem__(self, key)
    def __iter__(self):
        return dict.__iter__(self)
    def __len__(self):
        return dict.__len__(self)

    def update(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, got %d" % len(args))
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    def setdefault(self, key, value=None):
        if key not in self:
            self[key] = value
        return self[key]

class typelistdict(listdict):
    def __init__(self,typ=None):
        if typ :
            self.typ=typ
        else:
            return {}

    def __setitem__(self, key, value):
        if isinstance(key,self.typ):
            dict.__setitem__(self,key,value)
        else :
            raise TypeError( "Wrong type in list type dict of type"+ str(self.typ))

    def update(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, got %d" % len(args))
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]
