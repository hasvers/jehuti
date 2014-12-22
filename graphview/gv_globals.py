import pygame as pg
from pygame import surface as pgsurface, event as pgevent, sprite as pgsprite, rect as pgrect,mixer as pgmixer
from copy import deepcopy
from numpy import array, random as nprandom, ndarray,nditer, uint8 as npuint8, int as npint,maximum as npmaximum,newaxis as npnewaxis
from math import *
import colors as matcolors
import random as rnd
import cPickle as pickle
import gradients
from clotools import sparse, sparsemat, listdict
import debug
from operator import itemgetter,attrgetter
import networkx as nx
import cProfile,pstats,sys,time,itertools,re
import os
from PIL import Image as pilImage, ImageEnhance as pilImageEnhance
from PIL import ImageOps as pilImageOps, ImageFilter as pilImageFilter

from itertools import chain as iterchain

pg.font.init()
pgmixer.init(44100)
colorconverter=matcolors.ColorConverter()
profiler=cProfile.Profile()

def prolog(fname):
    stats=[[i.code ,i.totaltime,i.inlinetime,i.callcount,i.reccallcount] for i in profiler.getstats()]
    stats=sorted(stats,key=lambda e:e[2],reverse=1)
    with fopen(fname,'w') as prolog:
        for i in stats:
            if not i:
                continue
            st=' '.join([str(z) for z in  i])
            prolog.write(st+'\n')

class Clipboard(object):
    def copy(self,txt):
        pg.scrap.put('TEXT',txt)
    def paste(self):
        return pg.scrap.get('TEXT')

clipboard=Clipboard()

clock = pg.time.Clock()


#class MyPickler (pickle._Pickler):
    #def save(self, obj):
        #print 'pickling object', obj, 'of type', type(obj)
        #pickle.Pickler.save(self, obj)

pretty= True
RGBACanvas=False
if RGBACanvas :
    COLORKEY =(0,0,0,0)
    Canvasflag=pg.SRCALPHA
else :
    COLORKEY=(255,0,0,0)
    Canvasflag=0

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

def olistdir(path):
    return sorted([i for i in os.listdir( os.path.normpath(resource_path(path) )) if i[0]!='~' ])

def image_load(path):
    return pg.image.load(os.path.normpath(resource_path(path)) )

def fopen(path,*args):
    return open(os.path.normpath(resource_path(path)),*args)

def print_arbor(path):
    for i in olistdir(path):
        np=os.path.join(path,i)
        if os.path.isdir(np):
            print np
            if not i in (path,'.','..'):
                print_arbor(np)
        else:
            print '                   ',np
            continue

database={}
database['basepath']='./'
database['basepath']=os.path.normpath(resource_path(database['basepath']))

graphic_chart={}
ergonomy={}
sound_bank={}
evtyp={'sound_bank':"pgmixer.Sound( 'SRC/snd/###' )"}


def confload(fname): #Very nasty way of loading the .ini
    if fname!='database':
        exec('global '+fname+'\n'+fname+'={}')
    entry=eval(fname)
    try :
        f = fopen(os.path.join(database['basepath'],fname+'.ini'),'rU')
    except :
        f = fopen(os.path.join(database['srcpath'],fname+'.ini'),'rU')
    text='''{}'''.format(f.read())
    pats=re.findall("\[.*?\]=",text)
    for p in pats:
        text=text.replace(p,fname+p)
    if fname in evtyp:
        for line in text.split('\n'):
            ls=line.split('=',1)
            if len(ls)>1:
                try:
                    text=text.replace(line,ls[0]+'={}'.format(evtyp[fname].replace(
                        'SRC/',database['basepath']).replace('###',ls[1])))
                except:
                    text=text.replace(line,ls[0]+'={}'.format(evtyp[fname].replace(
                        'SRC/',database['srcpath']).replace('###',ls[1])))

    exec(text)
    f.close()
    return entry

database=confload('database')
basepath=database['basepath']
srcpath=database['srcpath']
for i, j in tuple(database.iteritems()):
    if isinstance(j,basestring) and (basepath in j or srcpath in j or './' in j):
        database[i]=resource_path(j)


from gv_fonts import FontMaster
fonts=FontMaster(database,resource_path)
basefont= fonts["base"]

for fname in database['modules']:
    confload(fname)

"""loader = fopen(database['basepath']+'loader.ini','rU')
for i in loader :
    j=i.strip().split('#')
    if j[0]:
        print 'Loading '+j[0]
        exec( 'from '+j[0] +' import *')"""



icon_db={}
def load_icon(typ,**kwargs):
    if typ=='node':
        try:
            if not 'node' in icon_db:
                icon_db['node']=image_load(database['image_path']+'icons/node/base.png')
            return icon_db['node']
        except:
            return False

mycursor=pg.transform.smoothscale(pg.image.load(database['cursor_img']),database['cursor_size'])


def get_color(txt):
    text=txt.strip()
    if not text:
        return (0,0,0,0)
    if text[0]=='(' or text[0]=='[':
        try:
            tup=eval(text)
            if len(tup) ==4:
                return tup
            if len(tup)==3:
                return tup + (255,)

        except:
            return get_color(txt.translate(None,'()[]'))
    else:
        if text in ('r','R','red'):
            return (230,100,100,255)
        if text in ('y','Y','yelloz'):
            return (230,200,100,255)
        if text in ('g','G','green'):
            return (100,200,100,255)
        if text in ('b','B','blue'):
            return (100,100,200,255)
        if text in ('d','D','black'):
            return (0,0,0,255)
        if text in ('a','A','gray','grey'):
            return (140,140,140,255)
        if text in ('w','W','white'):
            return (255,255,255,255)
    return (0,0,0,0)



def pgu_writen(text,font,color,border=1):
    """Write text to a surface with a black border
    Adapted from Phil's PyGame Utilities"""
    w,h = font.size(text)+array((2,2))
    h=max(h,font.get_linesize()+2)
    if text.isspace():
        return pg.surface.Surface((w,h)+array((-4,0)),pg.SRCALPHA)
    s=pg.surface.Surface((w,h),pg.SRCALPHA)
    # Render the text in black, at various offsets to fake a border
    pos = array((1,1))
    tmp = font.render(text,1,(0,0,0))
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for dx,dy in dirs:
        s.blit(tmp,(pos[0]+dx*border,pos[1]+dy*border))
    # Now render the text properly, in the proper color
    tmp = font.render(text,1,color)
    s.blit(tmp,pos)
    return s

def rint(nb):
    return int(round(nb))

def rfloat(nb):
    return round(nb*database['floatprecision'])/database['floatprecision']

def rftoint(nb):
    return int(round(nb*database['floatprecision']))

def shallow_nested(item,make_new=0,**kwargs):
    exclude=kwargs.get('exclude',() )
    #Makes shallow copies of all containers at all levels while conserving all non-containers
    if hasattr(item,'nested_copy'):
        if not item.nested_copy:
            #Tricky: I want databits to be duplicable (e.g. script effect)
            # but not dataitems that serve as reference (e.g. node),
            # neither fields contained in those dataitems
            make_new=0
        else:
            make_new=1
    if hasattr(item,'iteritems'):
        new= item.__class__()
        new.update({ shallow_nested(i,make_new,**kwargs):shallow_nested(j,make_new,**kwargs) for i,j in item.iteritems()})
        return new
    if hasattr(item,'__iter__'):
        try:
            hash(item) #if item is immutable
            return item
        except:
            pass
        if type(item)==ndarray:
            return item
        new= item.__class__()
        for i in item :
            new+=  item.__class__( ((shallow_nested(i,make_new,**kwargs)), ))
        return new
    if make_new and hasattr(item,'__dict__') :
        if hasattr(item,'copy'):
            return item.copy()
        try:
            new= item.__class__()
            print 'Shallow_nested: Making new', item.__class__.__name__
        except:
            raise Exception( "Shallow_nested: Couldn't make new", item.__class__.__name__)
        for i,j in item.__dict__.iteritems():
            if not i in exclude:
                if isinstance(j,nx.Graph):
                    print 'Shallow_nested: Cannot replicate networkx.Graph securely.'
                    new.__dict__[i]=j.__class__()
                if True in [hasattr(j,k) for k in ('iteritems','nested_copy','__iter__')]:
                    new.__dict__[i]=shallow_nested(j,make_new,**kwargs)
        return new
    if 'meth' in kwargs:
        return kwargs['meth'](item)
    return item
