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
            for fil in olistdir(self.basepath+self.preload_folder,self.ext):
                self.load(fil,relpath=self.preload_folder )

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


    def __init__(self,**kwargs):
        ResourceLibrary.__init__(self,**kwargs)
        size=FONTLIB['base'].get_linesize()
        s=pg.surface.Surface((size,size),pg.SRCALPHA)
        s.fill((0,0,0,0))
        self.buffer["none"]=s
        self.buffer["mycursor"]=pg.transform.smoothscale(
            pg.image.load(database['cursor_img']),database['cursor_size'])


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
        ext=self.ext
        if not '.' in ext:
            ext='.'+ext
        name=name.split(ext)[0]
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


class WindowSkinLibrary(ResourceLibrary):

    typ='image'
    folder='skins/'
    ext='png'

    class Skin(object):
        '''Class that contains'''
        skin=None
        border=None
        mode='scale'

    def load(self,name,**kwargs):
        fname=name
        if '_skin' in name:
            name=fname.split('_skin')[0]
            attr='skin'
        elif '_border' in name:
            name=fname.split('_border')[0]
            attr='border'
        else:
            return False
        if name in self.buffer:
            if getattr(self.buffer[name],attr):
                return self.buffer[name]
        else:
            self.buffer[name]=self.Skin()
        relpath=kwargs.get('relpath',None)
        if relpath is None:
            relpath=self.preload_folder
        buff=image_load(self.basepath+relpath+fname)
        setattr(self.buffer[name],attr,buff)
        return self.buffer[name]

WINSKINLIB=WindowSkinLibrary(preload='./')


class CanvasIconLibrary(ResourceLibrary):

    typ='image'
    folder='icons/'
    ext='png'

    def get_icon(self,typ,klass,**kwargs):
        icon_db=self.buffer
        if typ=='node':
            nbimgs=20
            val=kwargs.get('val',1.)
            unsat=kwargs.get('unsat',0)
            intval=int(round(nbimgs*val))
            #try:
            term='node'+str(intval)
            if unsat:
                term+='u'
            if not term in icon_db:
                try:
                    icon_db[term]=image_load(self.basepath+'node/{}.{}'.format(term,self.ext))
                except:
                    rad=graphic_chart['node_base_size']
                    size=(rad*2,rad*2)
                    icon_db[term]=klass().make_icon(size,rad,
                        graphic_chart['icon_node_fill_colors'],intval/float(nbimgs),unsat).convert_alpha()
                    pg.image.save(icon_db[term],self.basepath+'node/{}.{}'.format(term,self.ext))
            return icon_db[term]
        return False

            #try:
                #if not 'node' in icon_db:
                    #icon_db['node']=image_load(self.basepath+'node/base.png')
                #return icon_db['node']
            #except:
                #pass
CANVAS_ICON_LIB=CanvasIconLibrary()

