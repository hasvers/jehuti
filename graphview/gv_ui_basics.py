from gv_resources import *
from gv_threadevents import *
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
        self.ui.set_mouseover(txt,anim,**kwargs)

    def kill_mouseover(self):
        self.ui.kill_mouseover()

    def react(self,evt):
        if 'anim' in evt.type:
            if evt.args[0].item==self.mouseover and 'stop' in evt.type:
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
        self.children=[] #Children of UI_Item allow multipart sprites.
        self.floating=[] #Children that do not have a fixed relative position
        self.float_type=kwargs.get('float_type','dft')#among: lin,arc,rot
        #Type of arrangement for floating children
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

    def add_child(self,child,epos=None):
        self.children.append(child)
        if epos:
            basepos=epos
            self.pos[child]=basepos
            #child.rect.center=array(self.rect.topleft)+basepos
        else:
            self.floating.append(child)
            self.repos_children()
        #child.parent=self #first try without this
        return self.pos[child]

    def repos_children(self,clear=False):
        if not self.floating:
            return
        if clear:
            #Remove dead children
            for c in tuple(self.floating):
                if not c.alive():
                    self.floating.remove(c)
            if not self.floating:
                return
        size=array(self.rect.size)
        nc=len(self.floating)
        typ=self.float_type
        if typ=='dft':
            if nc<3:
                typ='lin'
            else:
                typ='arc'
        effsize=graphic_chart['effect_base_size']
        if typ=='lin':
            basepos= (size*.1)+(0,-effsize)
        elif typ=='arc':
            basepos=size/2
            rad=  size*.5+effsize
        elif typ=='rot':
            #TODO: should be an animation instead
            t=pg.time.get_ticks()*2*pi/8000
            basepos=size/2
        else:
            basepos=array((0,0))
        for ic,c in enumerate(self.floating):
            if typ=='lin':
                self.pos[c]=basepos.copy().astype('int')
                basepos += (effsize*1.5,0)
            elif typ=='rot':
                tt=t+ ic*2*pi/nc
                self.pos[c]= (basepos + rad*(cos(tt ),-sin(tt ))).astype('int')
            elif typ=='arc':
                tt=pi/2
                if nc>1:
                    amp=pi/12.*nc
                    tt+=(1-ic*2./(nc-1))*amp
                self.pos[c]= (basepos + rad*( cos(tt),-sin(tt) )).astype('int')

    def upd_child(self):
        self.repos_children()
        for c in self.children:
            c.rect.center=self.abspos(c)

    def abspos(self,child=None,**kwargs):
        if not hasattr(self,'pos'):
            return (0,0)
        if child and child in self.pos :
            pos=array(self.pos[child])
            if self.parent :
                return tuple(self.parent.abspos(self)+pos)
            else :
                return tuple(self.rect.topleft+pos)
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


        mod=array((1.,1.,1.,1.))
        grayed=False
        for i in self.modimg:
            if self.states[i]:
                j=self.color_mod(i)
                if j=='grayed':
                    grayed=True
                else:
                    mod *= array(j)

        #Create a new surface only if something has changed
        if grayed or not (mod==tuple(1. for i in mod ) ).all():
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
            if grayed:
                image=convert_to_greyscale(image)

            #Separate the mod into alpha and color if necessary
            if not self.per_pixel_alpha:
                useflag=pg.BLEND_MULT
                modalp=mod[3]
                mod=mod[:3]
            else:
                useflag=pg.BLEND_RGBA_MULT

            #RGB/RGBA component
            if not (mod==tuple(1. for i in mod ) ).all():
                excess=tuple(max(0.,i-1.) for i in mod)
                if excess!=(0,0,0,0):
                    img=image.copy()
                    img.fill(tuple(min(255,int(i*255)) for i in excess),None,useflag)
                else :
                    img = None
                image.fill(tuple(min(255,int(i*255)) for i in mod),None,useflag)
                if img:
                    image.blit(img,(0,0),None,pg.BLEND_RGB_ADD)

            #Surface alpha
            if not self.per_pixel_alpha and modalp!=1:
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
        else:
            try:
                image=self.base_image.copy()
            except:
                image=self.images['idle'].copy()
            if  not self.per_pixel_alpha and self.alpha:
                image.set_alpha(self.alpha,pg.RLEACCEL)
        if self.states.get('blur',None):
            gv_effects.make_blur(image,self.blur_mode)
        self.image=image
        return self.image

    def set_state(self,state,force_redraw=False,**kwargs):
        #print 'set state',self,state,force_redraw
        if kwargs.get('recursive',False):
            for c in self.children:
                c.set_state(state,force_redraw,**kwargs)
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
