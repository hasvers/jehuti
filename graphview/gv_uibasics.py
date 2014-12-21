from gv_globals import *
from gv_threadevents import *
from gv_anims import *
import gv_effects

class User():
#User controls uniaue states in the UI : a single object can be grabbed or focused for keyboard actions at a time
#Non unique states such as hovering or selecting are controlled by each widget
    debug_mode=0
    profile_mode=0
    paused=0
    recording=0 #for video making
    last_recorded=0
    use_pil=0

    def __init__(self,**kwargs):
        self.state='idle'
        self.arrow=pgsprite.Sprite()
        self.arrow.rect=pgrect.Rect(0,0,4,4)
        self.arrow.radius=2
        self.arrow.mask=pg.mask.Mask((4,4))
        self.arrow.mask.fill()
        self.focused_on=None
        self.grabbed=None
        self.just_clicked=None #for double clicks
        self.status=None
        self.ui=None
        self.evt=EventCommander(self)
        self.evt_per_ui={}
        self.mouseover=None #Emote used for mouseover text
        self.screen_scale=1
        self.screen_trans=array((0,0))

    def pause(self,do=True):
        self.paused=do
        self.evt.paused=do

    def setpos(self,pos):
        self.arrow.rect.center=pos

    def focus_on(self,item):
        if self.focused_on:
            self.focused_on.rm_state('focus')
        self.focused_on=item
        if item :
            return item.set_state('focus')
        else :
            return False

    def unfocus(self):
        if self.focused_on :
            self.focused_on.rm_state('focus')
            self.focused_on=None
            return True
        else :
            return False

    def grab(self,item):
        self.kill_mouseover()
        if self.grabbed :
            self.grabbed.rm_state('grab')
        self.grabbed=item
        if item :
            return item.set_state('grab')
        else :
            return False

    def ungrab(self):
        if self.grabbed :
            self.grabbed.rm_state('grab')
            self.grabbed=None
            return True
        else :
            return False

    def set_ui(self,ui,kill=True,**kwargs):
        if kill:
            self.kill_ui(self.ui)
        self.ui=ui
        if not self.ui in self.evt_per_ui:
            self.evt_per_ui[self.ui]=EventCommander(self)
        self.evt=self.evt_per_ui[self.ui]
        if not kwargs.get('no_launch',False):
            self.ui.launch()
        return True

    def kill_ui(self,ui):
        if ui:
            ui.kill()
            del self.evt_per_ui[ui]

    def set_status(self,status):
        if self.status==status:
            return
        self.status=status
        try:
            evt=Event(affects=self, type='status')
            self.evt.pass_event(evt,self,True)
        except Exception as e:
            print e
            pass

    def set_mouseover(self,txt,anim=None,**kwargs):
        self.kill_mouseover()
        self.mouseover=Emote(txt,**kwargs)
        if anim:
            self.mouseover.set_anim(anim)
        user.ui.group.add(self.mouseover)
        self.mouseover.rect.bottomleft=user.mouse_pos()

    def kill_mouseover(self):
        if self.mouseover:
            self.mouseover.kill()
            self.mouseover=None

    def mouse_pos(self):
        return self.scale_vec(pg.mouse.get_pos())-self.screen_trans

    def mouse_rel(self):
        return self.scale_vec(pg.mouse.get_rel())

    def scale_vec(self,vec,invert=True):
        if self.screen_scale !=1:
            if invert:
                return tuple(rint(vec[i]/user.screen_scale) for i in (0,1))
            else:
                #only for blitting
                return tuple(rint(vec[i]*user.screen_scale) for i in (0,1))
        else:
            return vec

    def trigger_video(self):
        if self.recording:
            self.recording=False
            print 'Video off'
            self.video.close()
            self.video=None
        else:
            from ffmpegwriter import FFMPEG_VideoWriter
            print 'Video on'
            self.recording=True
            self.video=FFMPEG_VideoWriter(os.path.join(database['basepath'],'Video{}.mp4'.format(time.strftime("%c"))),
                 self.ui.screen.get_rect().size,
                 ergonomy['animation_fps'],"libx264")
        return 1

    def screenshot(self):
        import time
        try:
            print 'Screenshot taken'
            pg.image.save(self.ui.screen,os.path.join(database['basepath'],'Screenshot{}.png'.format(time.strftime("%c"))) )
        except Exception as e:
            print e
        return 1

    def add_video_frame(self,img=None,enhance=False):
        if img is None:
            img =self.ui.screen
        if ['show_cursor_on_video']:
            img.blit(mycursor,pg.mouse.get_pos())
        pil_string_image = pg.image.tostring(img, "RGB")
        if enhance:
            pil_image = pilImage.fromstring("RGB",img.get_rect().size,pil_string_image)
            enhancer=pilImageEnhance.Sharpness(pil_image)
            pil_image=enhancer.enhance(1.2)
            pil_string_image=pil_image.tostring()
            #new=pg.surfarray.array2d(img)
            #self.video.write_frame(new)
        self.video.write_frame(pil_string_image )#pg.image.tostring(img, "RGB"))
        return

    def debug(self,item):
        struct=None
        dic=None
        if hasattr(item,'debug'):
            deb=item.debug()
            if deb==None:
                return
            if hasattr( deb,'keys'):
                dic=deb
            elif hasattr(deb,'__iter__'):
                struct=tuple(deb)

        if not struct:
            if not dic:
                dic=item.__dict__
            struct=tuple(('{}:{}'.format(i,j), lambda:1) for i,j in dic.iteritems() )
        self.ui.float_menu(struct,scrollable='v')

user = User()

def convert_to_greyscale(image):
    array = pg.surfarray.pixels3d(image)
    iarray = array.astype(npint)
    # slicing hint from http://dmr.ath.cx/gfx/python/
    r = iarray[:, :, 0]
    g = iarray[:, :, 1]
    b = iarray[:, :, 2]
    # convert to greyscale by luminance
    gray = (30*r+59*g+11*b)/100
    gray = gray.astype(npuint8)
    array[:, :, 0] = gray
    array[:, :, 1] = gray
    array[:, :, 2] = gray
    return image



class UI_Item(pg.sprite.DirtySprite): #Base item for state management
    priority={'idle':0,'base':0,
              'hover':1,
              'focus':2,
              'select':2,
              'grab':3,
              'ghost':3,
              'disabled':4,
              'blur':8,
              'anim':9, #I want items to finish their animation before changing again
              'busy':10,
              }
    state = 'idle'
    state_list=('idle',)
    draggable=False
    sound=False
    anim_mod=(1,1,1,1) #animated modifier
    per_pixel_alpha=1
    blur_mode=graphic_chart['default_blur_mode'] #(margin, nb of repetitons,flag,total amplitude)

    #OPTIMIZATION: Clear modimg if necessary to improve runtime performance, however will cause storing many more pictures
    modimg=('base','hover','select','ghost')#states that translate as simple modifiers such as hover, select
    base_image=False #image of the current base state before modifiers

    def __init__(self,**kwargs):
        self.images={}
        super(UI_Item,self).__init__()
        self.states={'select':False,
              'hover':False,
              'grab':False,
              'ghost':False,
              'anim':False,
              'base':True} #Base is always true, allows permanent modifiers (e.g. link alpha)
        self.parent=None
        self.children=[] #Children of UI_Item allow multipart sprites. For interaction, use UI_Widget
        self.pos={}
        if kwargs.get('state',0):
            self.set_state(kwargs['state'],invisible=True)

    def __repr__( self ):
        return self.__class__.__name__  + str(hash(self))

    @property
    def is_grabbed(self):
        return self.states.get('grab',False)

    @property
    def is_focused(self):
        return self.states.get('focus',False)

    @property
    def is_hovering(self):
        return self.states.get('hover',False)

    @property
    def is_selected(self):
        return self.states.get('select',False)

    @property
    def is_ghost(self):
        return self.states.get('ghost',False)

    @property
    def is_disabled(self):
        return self.states.get('disabled',False)

    @property
    def is_animated(self):
        return self.states.get('anim',False)

    @property
    def idle(self):
        if self.state =='idle':
            return True
        else:
            return False

    def add_child(self,child=None,epos=None):
        #If no child given, simply repositions children
        basepos= array(array(self.rect.size)*(.1,.1),dtype='int')
        reboot=False
        for em,pos in tuple(self.pos.iteritems()):
            if not em.alive():
                reboot=True
                del self.pos[em]

        for c in self.children:
            if reboot or not c in self.pos:
                self.pos[c]=basepos
            basepos += (16,0)
            #em.rect.center=array(self.rect.topleft)+pos
        if child:
            if epos:
                basepos=epos
            elif child in self.pos:
                basepos=self.pos[child]

            self.pos[child]=basepos
            child.rect.center=array(self.rect.topleft)+basepos
            self.children.append(child)
            #child.parent=self #first try without this
        return basepos

    def upd_child(self):
        for c in self.children:
            c.rect.center=self.abspos(c)

    def abspos(self,child=None,**kwargs):
        if not hasattr(self,'pos'):
            return (0,0)
        if child and child in self.pos :
            if self.parent :
                return tuple(array(self.parent.abspos(self))+array(self.pos[child]))
            else :
                return tuple(array(self.rect.topleft)+array(self.pos[child]))
        else :
            if self.parent :
                return self.parent.abspos(self)
            else :
                return self.rect.topleft
    def mousepos(self,child=None):
        return tuple(array(user.mouse_pos())-array(self.abspos(child)))


    def set_image(self,state):
        #print 'set image',self,state
        ## Comments with ## = potential breaking change, 2013-08-05
        if not self.images:
            return False
        if state in self.images:
            self.base_image=self.images[state]
            ##return self.image
        else:
            state,prior =  sorted([(i,self.priority.get(i,0))
                for i in self.images if i =='idle' or self.states.get(i,0)],
                key=itemgetter(1),reverse=1)[0]
            self.base_image=self.images[state]

        if self.per_pixel_alpha:
            try:
                image=self.base_image.convert_alpha()
            except:
                image=self.images['idle'].convert_alpha()
        else:
            try:
                surf=self.base_image
            except:
                surf=self.images['idle']
            image=pgsurface.Surface(surf.get_rect().size,pg.SRCALPHA)
            image.blit(surf,(0,0))

        mod=array((1.,1.,1.,1.))
        for i in self.modimg:
            if self.states[i]:
                j=self.color_mod(i)
                if j=='grayed':
                    image=convert_to_greyscale(image)
                else:
                    mod *= array(j)

        if not self.per_pixel_alpha:
            useflag=pg.BLEND_MULT
            modalp=mod[3]
            mod=mod[:3]
        else:
            useflag=pg.BLEND_RGBA_MULT

        excess=tuple(max(0.,i-1.) for i in mod)
        if excess!=(0,0,0,0):
            img=image.copy()
            img.fill(tuple(min(255,int(i*255)) for i in excess),None,useflag)
        else :
            img = None
        image.fill(tuple(min(255,int(i*255)) for i in mod),None,useflag)
        if img:
            image.blit(img,(0,0),None,pg.BLEND_RGB_ADD)


        if not self.per_pixel_alpha:
            surf=surf.convert()
            surf.fill(COLORKEY)
            surf.blit(image,(0,0))
            image=surf
            image.set_colorkey(COLORKEY)
            if self.alpha:
                basalp=self.alpha
            else:
                basalp=255
            image.set_alpha(rint(modalp*basalp),pg.RLEACCEL)

            #try:
                #if self.alpha and not self.states['anim']:
                    #image.set_alpha(self.alpha,pg.RLEACCEL)
            #except:
                #pass

        if self.states.get('blur',None):
            gv_effects.make_blur(image,self.blur_mode)
        self.image=image
        return self.image

    def set_state(self,state,force_redraw=False,**kwargs):
        #print 'set state',self,state,force_redraw
        if self.is_disabled and state != 'anim':
            return False
        if state == 'idle':
            for i in self.states.keys():
                if i!='base':
                    self.states[i] = False
            self.set_image(state)

            return True
        if state in self.states and self.states[state] and not force_redraw:
            #TODO : check whether 'and not force_redraw' messed something up! (added aug 2013)
            return False
        self.states[state]=True

        ekwargs={'type':state,'item':self,'affects':user}
        #TODO: affects=user is a somewhat hackish way to get sound effects
        if self.sound:
            ekwargs['sound']=state
        if not kwargs.get('invisible',0):
            user.evt.pass_event(Event(**ekwargs),self,True)


        if state in self.modimg:
            force_redraw=True
        if self.priority[state] > self.priority[self.state]:
            self.state=state
            force_redraw=True
        if force_redraw :
            #try :
            self.set_image(state)
            #except:
            #    pass
            return 'visible'
        else:
            return True

    def rm_state(self,state,force_redraw=False,**kwargs):
        if not state in self.states or self.states[state] == False:
            return False
        self.states[state]=False
        if state in self.modimg or force_redraw:
            self.set_image(self.state)
        if self.state == state :
            self.state='idle'
            for i,j in self.states.iteritems():
                if j and self.priority[i]> self.priority[self.state] :
                        self.state =i

            self.set_image(self.state)
            return 'visible'
        else :
            return True

    def event(self,*args,**kwargs):
        return False

#    def update(self,*args,**kwargs):
#        return False

    def update(self):
        if self.children:
            self.upd_child()
        #if self.states['anim']:
            #if not self.current_anim:
                #self.rm_state('anim')

    def kill(self,recursive=False):
        if not self.alive() and not recursive:
            return False
        if recursive:
            for c in self.children :
                c.kill(recursive)
        super(UI_Item,self).kill()
        return True


    def set_anim(self,anim,**kwargs):
        for c in [self]+self.children:
            if not 'anim' in c.modimg:
                c.modimg+='anim',
        kwargs.setdefault('affects',(self.parent,) )
        user.ui.anim.add_anim(self,anim,**kwargs)
        return True

    def set_anim_mod(self,anim_mod,recursive=True):
        self.anim_mod=anim_mod
        if recursive:
            for c in self.children:
                c.set_anim_mod(anim_mod,recursive)

    def color_mod(self,state):
        if state == 'anim':
            return self.anim_mod
        else :
            return (1.,1.,1.,1.) #override this part in subclass

    def add_to_group(self,group):
        [c.add_to_group(group) for c in self.children]
        if self in group :
            return False
        if hasattr(self,'layer') :
            try:
                group.add(self,layer=self.layer)
            except:
                group.add(self)
        else :
            group.add(self)
        return True

    def rem_from_group(self,group):
        [c.rem_from_group(group) for c in self.children]
        if not self in group :
            return False
        group.remove(self)
        return True


class UI_Widget(UI_Item):
# Widget that may contain other elements and controls non unique states such as hovering and selection over its children
# (hovering is horizontally unique (among children of a single widget) but vertically propagated from parent to child)

    select_opt={'default_multi':False}
    name='widget'
    #options for how selection works: default_multi = no exclusive selected state

    def __init__(self,*args,**kwargs):
        UI_Item.__init__(self,**kwargs)
        for i,j in kwargs.iteritems():
            if i=='parent':
                self.parent=j
        self.selected=None
        self.multiseld=[]
        self.hovering=None

    def update(self):
        #if self.states['anim']:
            #self.animate()
            #return True
        return False

    def kill(self,recursive=False):

        self.unselect()
        self.unhover()
        for c in self.children :
            if c.is_focused:
                user.unfocus()
            if recursive :
                c.kill()
        if recursive:
            self.children=[]
        return UI_Item.kill(self)

    def set_anim_mod(self,anim_mod,recursive=False):
        UI_Item.set_anim_mod(self,anim_mod,recursive)

    def event(self,event,*args,**kwargs):
        if self.is_disabled:
            return False
        handled=False
        refpos=array(kwargs.pop('refpos',self.abspos('child',with_offset=False)))
        children=kwargs.pop('children',self.children)
        hovering = False
        if event.type in (pg.MOUSEMOTION,pg.MOUSEBUTTONDOWN,pg.MOUSEBUTTONUP):
            pos = tuple( array(event.pos)-refpos )
            newhover=False
            for c in children[::-1] :
                if c.rect.collidepoint(pos):
                    hovering =True
                    if self.hover(c) :
                        newhover = c
                    if c.event(event) :
                        self.dirty=1
                        return True
                    break
            if hovering ==False :
                if self.hovering and self.hovering in children:
                    self.unhover()
            if  newhover:# or self.unhover() :
                self.update()

        elif event.type==pg.KEYDOWN:
            if self.keymap(event):
                handled= True

        #if hovering:
            #handled= True
        if handled:
            self.dirty=1
        return handled


    def keymap(self,event,**kwargs):
        #Overwrite to manage keyboard events
        return False

    def select(self,item):
        if self.select_opt['default_multi']:
            return self.multisel(item)
        if self.selected :
            if self.selected != item :
                self.selected.rm_state('select')
            else :
                item.rm_state('select')
                self.selected=None
                return True
        self.selected=item
        if item :
            return item.set_state('select')
        else :
            return False

    def multisel(self,item):
        if item :
            if not item in self.multiseld :
                self.multiseld.append(item)
                return item.set_state('select')
            else :
                self.multiseld.remove(item)
                return item.rm_state('select')
        else :
            return False


    def unselect(self, item=None):
        if self.selected and (item is None or item is self.selected) :
            self.selected.rm_state('select')
            self.selected= None
            return True
        if self.multiseld :
            if item :
                self.multiseld.remove(item)
                return item.rm_state('select')
            else :
                for i in self.multiseld :
                    i.rm_state('select')
                self.multiseld=[]
                return True
        return False

    def hover(self,item):
        if self.hovering:
            if self.hovering ==item :
                return False
            self.hovering.rm_state('hover')
        self.hovering=item
        pg.mouse.set_cursor(*pg.cursors.arrow)
        if self.hovering.draggable:
            pg.mouse.set_cursor(*pg.cursors.diamond)

        if item :
            if item.set_state('hover'):
                self.dirty=1
                return True
        else :
            return False

    def unhover(self):
        if self.hovering :
            self.hovering.rm_state('hover')
            self.hovering=None
            pg.mouse.set_cursor(*pg.cursors.arrow)
            self.dirty=1
            return True

        else :
            return False

    def rm_state(self,state):
        if UI_Item.rm_state(self,state) :
            if state =='hover':
                for c in self.children :
                    c.rm_state(state)
            return True
        return False

    def signal(self,signal,*args,**kwargs):
        kwargs.setdefault('affects',self)
        event=Event(*args,type=signal,source=self.name,**kwargs)
        if user.ui:
            user.evt.pass_event(event,self,True)


class UI_Icon(UI_Item):
    """Class for anything that behaves as a static icon for some entity,
    and therefore can have multiple sets of images depending on the state
    of said entity (node, link and so on)"""

    mutable=False #For icons that can be rotated, mirrored or resized
    ref_image=None #Image after modifiers but before mutation

    for i in ('angle','mirrorx','mirrory', 'zoom'):
        exec('_'+i+'''=False
@property
def '''+i+'''(self):
    return self._'''+i+'''

@'''+i+'''.setter
def '''+i+'''(self,val):
    if val!=self._'''+i+''':
        self._'''+i+'''=val
        self.mutate()
        ''')

    def __init__(self,**kwargs):
        self.image_sets={}
        self.set_to_create=set([])
        self.set=None
        UI_Item.__init__(self,**kwargs)
        self.emotes={} #current living emotes and their positions
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

    def set_image(self,value):
        self.ref_image= UI_Item.set_image(self,value)


    def set_state(self,state,force_redraw=False,**kwargs):
        test=UI_Item.set_state(self,state,force_redraw,**kwargs)
        if test :
            self.mutate()
        return test

    def rm_state(self,state,force_redraw=False,**kwargs):
        test=UI_Item.rm_state(self,state,force_redraw,**kwargs)
        if test :
            self.mutate()
        return test

    def mutate(self):
        if self.mutable: #and self.state in self.images :
            img=self.ref_image
            if not img:
                return False
            #img=self.images[self.state]
            if self.zoom :
                img=pg.transform.scale(img,tuple(int(x) for x in array(self.size)*self.zoom))
            elif img.get_rect().size != self.size:
                img=pg.transform.scale(img,self.size)
            if self.angle :
                img=pg.transform.rotate(img,self.angle)
            if self.mirrorx or self.mirrory:
                img=pg.transform.flip(img,self.mirrorx,self.mirrory)
            self.image=img
            sz=img.get_rect().size
            if sz!=self.rect.size:
                old=self.rect.center
                self.rect.size=img.get_rect().size
                self.rect.center=old
            return True
        for c in self.children :
            c.rect.center=self.abspos(c)
            c.mutate()
        return False



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

    color=(255,255,255,255)
    def __init__(self,contents,*args, **kwargs):
        self.type='emote'
        self.font=fonts["emote"]
        UI_Icon.__init__(self,**kwargs)
        self.set='idle'
        if not hasattr(contents,'__iter__'):
            contents=[contents]
        self.contents=contents
        self.make_contents()

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
        #img.fill( (255,0,0,255) )
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
