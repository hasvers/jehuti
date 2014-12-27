# -*- coding: utf-8 -*-
#Recipes from Daniel Brodie and Ken Seehof
"""Useful to extend this library :
class AlreadyExistingClass:
    __metaclass__=ExtendInplace

    def newmethod():
"""
def get_obj(name): return eval(name)

import new


def extend_method(klass,meth, newmeth):
    #the new method should have the old one as first argument
    ki = getattr(klass,meth)
    setattr(klass,meth, new.instancemethod(
        lambda *args, **kwds: newmeth(ki, *args, **kwds),None,klass))

def extend(class_to_extend):
    def decorator(extending_class):
        for i, j in extending_class.__dict__.iteritems():
            try :
                setattr(class_to_extend,i,j)
            except :
                pass
        return class_to_extend
    return decorator

class ExtendInplace(type):
    def __new__(self, name, bases, dict):
        prevclass = get_obj(name)
        del dict['__module__']
        del dict['__metaclass__']

        # We can't use prevclass.__dict__.update since __dict__
        # isn't a real dict
        for k,v in dict.iteritems():
            setattr(prevclass, k, v)
        return prevclass

class ExtendReplace(type):
    def __new__(self, name, bases, dict):
        prevclass = get_obj(name)
        del dict['__module__']
        del dict['__metaclass__']
        dict.update(prevclass.__dict__)
        ret =  type.__new__(self, name, prevclass.__bases__, dict)
        return ret
