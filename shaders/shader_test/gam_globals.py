import pygame as pg
from numpy import array


def rint(nb):
    return int(round(nb))

def rfloat(nb):
    return round(nb*database['floatprecision'])/database['floatprecision']

def rftoint(nb):
    return int(round(nb*database['floatprecision']))
    
def resource_path(fname,*args,**kwargs):
    return '../../shaders/' +fname



