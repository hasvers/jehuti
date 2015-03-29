# -*- coding: utf-8 -*-

from gv_ui_basics import *
from gv_anims import *

'''Classes derived from ui_basics (Especially UI_Item) that do not need
to be used by everything but still fill a very general purpose.'''



class UI_Icon(UI_Item):
    """Class for anything that behaves as a static icon for some entity,
    and therefore can have multiple sets of images depending on the state
    of said entity (node, link and so on)"""

    ref_image=None #Image after modifiers but before mutation
    maskable=True #Create a mask


    def __init__(self,**kwargs):
        self.image_sets={}
        self.set_to_create=set([])
        self.set=None
        UI_Item.__init__(self,**kwargs)
        self.emotes={} #current living emotes and their positions
        self.hotspot={} #Anchor for bubbles and emotes
        #self.image_sets={}
        for i, j in kwargs.iteritems():
            if hasattr(self,i):
                setattr(self,i,j)

    @property
    def images(self):
        return self.image_sets[self.set]

    @images.setter
    def images(self,value):
        self.image_sets[self.set]=value

    def kill(self,recursive=True):
        UI_Item.kill(self,recursive)


    def set_hotspot(self,spot,typ="default"):
        self.hotspot[typ]=spot

    def get_hotspot(self,emote=None,*args,**kwargs):
        #anchor for emotes and other interactive properties
        #if emotes anchored already, move the anchor point
        if emote in self.hotspot:
            return self.hotspot[emote]
        elif "default" in self.hotspot:
            return self.hotspot["default"]
        #generic anchor:
        basepos= array(self.rect.size)*(-.1,.1)
        if not emote:
            return array(self.rect.topright)+ basepos

        for em,pos in tuple(self.emotes.iteritems()):
            if not em.alive():
                del self.emotes[em]
                continue
            if (pos == basepos).all():
                basepos += (0,20)
        self.emotes[emote]=basepos
        return array(self.rect.topright)+basepos

    def set_image(self,value,**kwargs):
        self.ref_image= UI_Item.set_image(self,value,mutate=False)
        if kwargs.get('mutate',False):
            self.mutate()

    def select_set(self,setid):
        if setid in self.image_sets and setid != self.set:
            self.set=setid
            if setid in self.set_to_create:
                self.create(None,setid)
            self.set_state(self.state,True)
            return True
        return False

    def delete_set(self,setid):
        if setid in self.set_to_create:
            self.set_to_create.remove(setid)
        if setid in self.image_sets :
            del self.image_sets[setid]
            if self.set==setid :
                if self.image_sets :
                    self.select_set (self.image_sets.keys()[0])
            return True
        return False

    def color_mod(self,state):
        if state == 'anim':
            return self.anim_mod #return UI_Item.color_mod(self,state) if I change the way it works
        return graphic_chart.get('icon_'+state+'_color_mod',(1,1,1,1))

    def make_surface(self,size,mod,*args,**kwargs):
        return False

    def create(self,group,cset=None,**kwargs):
        #print 'create',self,group,cset
        if not cset:
            cset=self.set
        elif cset == 'all':
            for s in self.image_sets.keys():
                self.create(group,s)
            return True
        if not self.set:
            self.set=cset
        images = self.image_sets[cset] = {}
        states= self.state_list
        for state in states:
            if not state in self.modimg:
                images[state]=self.make_surface(self.size,self.color_mod(state),cset,**kwargs)

        #images['ghost']=images['idle'].copy()
        #images['ghost'].set_alpha(graphic_chart['ghost_alpha'])
        for img in images.values():
            if not (img.get_flags() & pg.SRCALPHA):
                img.set_colorkey(COLORKEY)

        if self.set == cset :
            self.base_image=None
            try :
                center=self.rect.center
            except :
                center= False
            self.set_image(self.state)
            self.rect=self.image.get_rect()
            self.size=self.rect.size
            if center :
                self.rect.center=center
        if group!=None :
            self.add_to_group(group)


    def call_emote(self,*args,**kwargs):
        em=Emote(*args,**kwargs)
        em.rect.center=self.get_hotspot(em)
        if not 'ephemeral' in kwargs:
            em.ephemeral=True
            em.set_anim('emote_jump')
        try:
            em.add_to_group(self.parent.group)
            em.add_to_group(self.parent.animated)
        except:
            print 'couldnt call emote', self, args,kwargs
            pass

class UI_IContainer(UI_Icon):
    mutable=True
    def __init__(self,**kwargs):
        self.size=array( (0,0) )
        UI_Icon.__init__(self,**kwargs)
        for c in self.children:
            if (array(c.size) >self.size).any():
                self.size=npmaximum(c.size,self.size)
            if not c in self.pos:
                self.pos[c]=array(self.size)/2

    def make_surface(self,size,mod,*args,**kwargs):
        return pg.surface.Surface(size,pg.SRCALPHA)

    def create(self,group,cset=None,**kwargs):
        UI_Icon.create(self,group,cset,**kwargs)
        for c in self.children:
            #try:
                c.create(group,cset,**kwargs)
            #except:
                #pass
                c.rect.center=self.abspos(c)

    def event(self,event,*args,**kwargs):
        return False
        for c in self.children:
            if c.event(event,*args,**kwargs):
                return True
        return False

class Emote(UI_Icon):
    #Picture or text or combination, meant to appear upon interaction with icons
    mutable=True
    sound=True
    ephemeral=False
    bg=None

    color=(255,255,255,255)
    def __init__(self,contents,*args, **kwargs):
        self.type='emote'
        self.font=FONTLIB["emote"]
        UI_Icon.__init__(self,**kwargs)
        self.set='idle'
        if not hasattr(contents,'__iter__'):
            contents=[contents]
        self.contents=contents
        self.make_contents()
        self.bg=kwargs.get('bg')

    def make_surface(self,*args,**kwargs):
        return self.image

    def set_contents(self,contents):
        oldrecenter=self.rect.center
        self.contents=contents
        self.make_contents()
        self.rect.center=oldrecenter

    def make_contents(self):
        padding=2
        imgs=[]
        hei,wid=0,0
        for c in self.contents:
            #contents given as text, even if they are pictures
            if '#' in c:
                opts=['']+c.split('#')[1::2]
                ws=c.split('#')[0::2]
            else :
                opts=['']
                ws=c,
            for wd in ws:
                if opts:
                    opt=opts.pop(0)
                if opt and opt[0]=='c':
                    try:
                        color=eval(opt[1:])
                    except:
                        color=get_color(opt[1:])
                else:
                    color=self.color
                if isinstance(color,basestring):
                    color=get_color(color)
                img=pgu_writen(wd,self.font,color)
                w,h=img.get_rect().size
                wid+=w+padding
                hei=max(hei,h)
                imgs.append(img)
        size=(wid,hei)
        images=self.image_sets[self.set]={}
        img=pgsurface.Surface(size ,pg.SRCALPHA )
        if self.bg:
            img.fill( self.bg )
        w=0
        for im in imgs:
            img.blit(im,(w,0))
            w+=im.get_rect().w
        images[self.state]=img
        self.set_image(self.state)
        self.rect =rect=self.image.get_rect()
        self.size=self.width,self.height=rect.size
        return True

    def update(self):
        UI_Item.update(self)
        if self.ephemeral:
            if not self.is_animated:
                self.kill()


    #def event(self,event):
        #if event.type == pg.MOUSEBUTTONDOWN :
            #if event.button==1 :
                #if self == user.just_clicked :
                    #user.just_clicked=None
                    #self.cast.handler.signal('edit',self.actor)
                #else :
                    #pg.time.set_timer(31,ergonomy['double_click_interval'])#just clicked remover
                    #user.just_clicked=self
                    #self.cast.select(self)
            #if event.button==3:
                #self.cast.handler.call_menu(self.cast.handler.menu())
            #return True

        #return False
##        return self.cast.event(event)
