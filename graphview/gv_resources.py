# -*- coding: utf-8 -*-
from gv_globals import *

class ResourceLibrary(object):
    '''Base class for objects that handle loading and caching
    of external resources (graphics,sound).'''

    typ=None #Type of resource that has a well defined path in database
    folder='' #Subfolder specific to this library within folder for resource type
    preload_folder=None #Sub-subfolder that is loaded from the start
    ext=None #extension of files accepted
    def __init__(self,**kwargs):
        self.buffer={}
        if 'preload' in kwargs:
            self.preload_folder=kwargs['preload']
        if self.typ and not self.ext:
            self.ext=database.get('{}_ext'.format(self.typ),None)

        if self.typ:
            self.basepath=database['{}_path'.format(self.typ)]+self.folder
        else:
            self.basepath=database['basepath']+self.folder

        if self.preload_folder:
            for name in olistdir(self.basepath+self.preload_folder,self.ext):
                self.load(name,relpath=self.preload_folder )

    def load(self,name,**kwargs):
        if name in self.buffer:
            return self.buffer[name]


    def __getitem__(self,name):
        if name in self.buffer:
            return self.buffer[name]
        else:
            for n in self.buffer:
                if name == n.split('.')[0]: #drop extension
                    return self.buffer[n]
        raise Exception('Resource not found: {}'.format(name))

    def __contains__(self,name):
        return name in self.buffer


class IconLibrary(ResourceLibrary):

    typ='image'
    folder='icons/'
    ext='png'

    def load(self,name,**kwargs):
        if name in self.buffer:
            return self.buffer[name]
        relpath=kwargs.get('relpath',None)
        size=kwargs.get('size',FONTLIB['base'].get_linesize())
        if relpath is None:
            relpath=self.preload_folder
        buff=image_load(self.basepath+relpath+name)
        buff=self.icon_draw(buff,kwargs.get('color',graphic_chart['icon_color']),1 )
        if not hasattr(size,'__iter__'):
            bsize=array(buff.get_rect().size)
            buff=pg.transform.smoothscale(buff,array(bsize)*4/5)
            r=buff.get_rect()
            img=pg.surface.Surface((max(bsize),max(bsize)),0,buff )
            img.blit(buff, img.get_rect().center-array(r.center))
            buff=img
            size=(size,size)
        buff=pg.transform.smoothscale(buff,size)
        self.buffer[name]=buff
        return self.buffer[name]


    def icon_draw(self,icon,color,border=1):
        '''Draws icons in any color.'''
        size=array(icon.get_rect().size)+2*border
        s=pg.surface.Surface(size,pg.SRCALPHA)
        if border:
            blackicon=icon.copy()
            blackicon.fill((255,255,255,255),None,pg.BLEND_SUB)
            pos = array((1,1))*border
            dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            for dx,dy in dirs:
                s.blit(icon,(pos[0]+dx*border,pos[1]+dy*border))
            # Now render the text properly, in the proper color
        else:
            pos=(0,0)
        coloricon=icon.copy()
        color = tuple(color[:3])+(0,)
        coloricon.fill(color,None,pg.BLEND_ADD)
        s.blit(coloricon,pos)
        return s

ICONLIB=IconLibrary(preload='./')