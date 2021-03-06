
from pygame import mask as pgmask, surfarray as pgsurfarray,cursors as pgcursors, PixelArray as pgPixelArray
import pygame_sdl2
#pygame_sdl2.import_as_pygame()
import pygame as pg
from pygame import surface as pgsurface, event as pgevent, sprite as pgsprite, rect as pgrect,mixer as pgmixer
from copy import deepcopy
from numpy import array,minimum,rint as nparint,clip as aclip
from numpy import random as nprandom, ndarray,nditer, uint8 as npuint8
from numpy import int as npint,maximum as npmaximum,newaxis as npnewaxis,abs as npabs
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
import shutil

from collections import OrderedDict
from itertools import chain as iterchain

pg.font.init()
#pgmixer.init(44100)
colorconverter=matcolors.ColorConverter()
profiler=cProfile.Profile()

def arint(*args,**kwargs):
    return nparint(*args,**kwargs).astype('int64')

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
        dft='TEXT'
        for typ in pg.scrap.get_types():
            if 'utf8' in typ.lower():
                dft=typ
                break
        pg.scrap.put(dft,txt.encode('utf-8'))
    def paste(self):
        dft='TEXT'
        for typ in pg.scrap.get_types():
            if 'utf8' in typ.lower():
                dft=typ
                break
        txt=pg.scrap.get(dft)
        return txt.decode('utf-8')

clipboard=Clipboard()

clock = pg.time.Clock()


#class MyPickler (pickle._Pickler):
    #def save(self, obj):
        #print 'pickling object', obj, 'of type', type(obj)
        #pickle.Pickler.save(self, obj)

pretty= True
RGBACanvas=True
if RGBACanvas :
    COLORKEY =(0,0,0,0)
    Canvasflag=pg.SRCALPHA
else :
    COLORKEY=(255,0,0,0)
    Canvasflag=0

database={}

def resource_path(relative,**kwargs):
    '''OS-agnostic version of relative path.'''
    genre=kwargs.get('filetype',None)
    if genre and genre+'_path' in database:
        path = database[genre+'_path']
        if path in relative:
            path=''
        if genre+'_ext' in database:
            ext=database[genre+'_ext']
            if not relative.endswith(ext):
                relative=relative+ext
    else:
        path=database['basepath']
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path ,relative)
    return os.path.join(path,relative)

def olistdir(path='',ext=None,with_path=False,filetype=None):
    '''OS-agnostic directory listing, restricted to files with extension ext.'''

    if filetype:
        if not ext and filetype+'_ext' in database:
            ext=database[filetype+'_ext']
        fpath=filetype+'_path'
        if fpath in database and not database[fpath] in path :
            path = os.path.join(database[fpath],path)
    if ext:
        if isinstance(ext,basestring):
            ext=[ext]
        ext=[e if e[0]=='.' else '.'+e for e in ext]

    path=os.path.normpath(resource_path(path) )
    tmp= sorted([i for i in os.listdir( path) if i[0]!='~'
        and (not ext or True  in [i.endswith(e) for e in ext]) ])
    if with_path:
        tmp=[os.path.join(path,i) for i in tmp]
    return tmp


def image_load(path):
    return pg.image.load(os.path.normpath(resource_path(path)) )

def fopen(path,*args,**kwargs):
    return open(os.path.normpath(resource_path(path,**kwargs)),*args)

def fremove(path,**kwargs):
    return os.remove(os.path.normpath(resource_path(path,**kwargs)))

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

database['basepath']='./'
database['basepath']=resource_path(database['basepath'])

graphic_chart={}
ergonomy={}
sound_bank={}

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
    exec(text)
    f.close()
    return entry
    #if fname in evtyp:
        #for line in text.split('\n'):
            #ls=line.split('=',1)
            #if len(ls)>1:
                #try:
                    #text=text.replace(line,ls[0]+'={}'.format(evtyp[fname].replace(
                        #'SRC/',database['basepath']).replace('###',ls[1])))
                #except:
                    #text=text.replace(line,ls[0]+'={}'.format(evtyp[fname].replace(
                        #'SRC/',database['srcpath']).replace('###',ls[1])))
    #exec(text)
    #f.close()
    #return entry

database=confload('database')
basepath=database['basepath']
srcpath=database['srcpath']
for i, j in tuple(database.iteritems()):
    if isinstance(j,basestring) and (basepath in j or srcpath in j or './' in j):
        database[i]=resource_path(j)


from gv_fonts import FontMaster
FONTLIB=FontMaster(database,resource_path)
basefont= FONTLIB["base"]

for fname in database['modules']:
    confload(fname)

"""loader = fopen(database['basepath']+'loader.ini','rU')
for i in loader :
    j=i.strip().split('#')
    if j[0]:
        print 'Loading '+j[0]
        exec( 'from '+j[0] +' import *')"""

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
            return get_color(txt.translate({ch:'' for ch in '()[]'}))
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
    if border:
        pos = array((1,1))*border
        tmp = font.render(text,1,(0,0,0))
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for dx,dy in dirs:
            s.blit(tmp,(pos[0]+dx*border,pos[1]+dy*border))
        # Now render the text properly, in the proper color
    else:
        pos=(0,0)
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
    if hasattr(item,'immutable'):
        if not item.immutable:
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
                if True in [hasattr(j,k) for k in ('iteritems','immutable','__iter__')]:
                    new.__dict__[i]=shallow_nested(j,make_new,**kwargs)
        return new
    if 'meth' in kwargs:
        return kwargs['meth'](item)
    return item



class Path(str):
    '''Strings that represent filesystem paths.
    Overloads __add__:
     - when paths are added, gives a path
     - when a string is added, gives a string'''
    def __add__(self,x):
        import os
        if isinstance(x,Path):
            return Path(os.path.normpath(os.path.join(str(self),x)))
        return os.path.normpath(os.path.join(str(self),x))

    def norm(self):
        import os
        return Path(os.path.normpath(str(self)))

    def osnorm(self):
        """Deal with different separators between OSes."""
        import os
        if os.sep=='/' and "\\" in str(self):
            return Path(os.path.normpath(str(self).replace('\\','/' )))
        elif os.sep=='\\' and "/" in str(self):
            return Path(os.path.normpath(str(self).replace('/','\\' )))
        else:
            return self.norm()

    def prev(self):
        import os
        lst=self.split()
        path=os.path.join(lst[:-1])
        return path.osnorm()

    def split(self):
        """"""
        import os
        lst=[]
        cur=os.path.split(self.norm())
        while cur[-1]!='':
            lst.insert(0,cur[-1])
            cur=os.path.split(cur[0])
        return lst

    def mkdir(self,rmdir=False):
        """Make directories in path that don't exist. If rmdir, first clean up."""
        import os
        if rmdir:
            os.rmdir(str(self))
        cur=Path('./')
        for intdir in self.split():
            cur+=Path(intdir)
            if not os.path.isdir(cur):
                os.mkdir(cur)

    def copy(self):
        return Path(self)

    def strip(self):
        '''Return string without final / or \\ to suffix/modify it.'''
        return str(self).strip('\/')


def interpret_input(event):

    mods=[]
    if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
        mods.append('CTRL')
    if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RALT,pg.K_LALT) )).any():
        mods.append('ALT')
    if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RSHIFT,pg.K_LSHIFT) )).any():
        mods.append('SHIFT')

    keys=[]
    if hasattr(event,'key'):
        keys.append(pg.key.name(event.key) )

    mouse=[]
    if hasattr(event,'button'):
        mouse.append(['','lclick','rclick','mclick','wheelup','wheeldown'][event.button] )

    return '+'.join(mods+keys+mouse)