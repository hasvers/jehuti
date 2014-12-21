# -*- coding: utf-8 -*-
from gam_cast_data import *
from gam_canvasicons import *


class ActorIcon(UI_Icon):
    mutable=True
    sound=True
    def __init__(self,cast,actor, **kwargs):
        super(ActorIcon, self).__init__()
        self.set='neutral'
        self.states['inactive']=False
        self.priority['inactive']=0
        self.modimg+='inactive',
        self.cast=cast
        self.actor = self.item=actor
        #self.curinfos={} #current infos to avoid recreating face if unnecessary
        self.make_faces()

    def event(self,event):
        if event.type == pg.MOUSEBUTTONDOWN :
            if event.button==1 :
                if self == user.just_clicked :
                    user.just_clicked=None
                    self.cast.handler.signal('edit',self.actor)
                else :
                    pg.time.set_timer(31,ergonomy['double_click_interval'])#just clicked remover
                    user.just_clicked=self
                    self.cast.select(self)
            if event.button==3:
                self.cast.handler.call_menu(self.cast.handler.menu())
            return True

        return False
#        return self.cast.event(event)

    def make_faces(self,face=None,source=None):
        actor = self.actor
        infos={}
        infos.update(actor.dft)
        infos.update(self.cast.handler.get_info(actor))
        #if self.curinfos:
            #dif=0
            #for i in self.curinfos:
                #if infos.get(i,None)==self.curinfos[i]:
                    #dif=1
            #if not dif:
                #return self.image
        #self.curinfos={i:infos[i] for i in ('portrait','name') }

        portrait=infos['portrait']
        if not portrait:
                portrait=database['default_portrait']
        if not face :
            candidates=None
            portrait=portrait+'/'

            try:
                olistdir(database['portraits']+portrait)
            except:
                try:
                    candidates = olistdir(database['portraits']+infos['name'].lower()+'/')
                    portrait=infos['name'].lower()+'/'
                except:
                    portrait='unknown/'

            if not candidates:
                candidates = olistdir(database['portraits']+portrait)

            flist=tuple ( [(str(c).split('.')[0],database['portraits']+portrait+str(c)) for c in candidates])
            for i,j in flist :
                self.make_faces(i,j)
            return True
        if not source :
            candidates = olistdir(portrait)
            for c in candidates :
                if face in str(c) :
                    source = portrait+str(c)

        images=self.image_sets[face]={}
        img=image_load(source).convert_alpha()
        rect = array(img.get_rect().size)
        height = graphic_chart['portrait_height']
        rect *= float(height)/rect[1]
        img=images['idle']=pg.transform.smoothscale(img,tuple(int(i) for i in rect))
        images['ghost']=img.copy()
        images['ghost'].set_alpha(graphic_chart['ghost_alpha'])
        for img in images.values():
            img.set_colorkey(COLORKEY)
        self.set_image(self.state)
        rect=self.image.get_rect()
        self.size=rect.size
        try :
            if self.rect.size !=rect.size:
                self.rect.inflate_ip(*tuple(array(rect.size)-array(self.rect.size)))
        except :
            self.rect = rect
            self.rect.bottom=self.cast.parent.rect.bottom
        return True

    def color_mod(self,state):
        if state =='inactive':
            return 'grayed'
        return graphic_chart.get('actor_'+state+'_color_mod',UI_Icon.color_mod(self,state))
        #return UI_Icon.color_mod(self,state)

    def get_hotspot(self,*args,**kwargs):
        if kwargs.get('balloon',False):
            return self.cast.get_hotspot(self)
            #shift=array(self.rect.size)/10
            #if self.mirrorx:
                #return self.rect.topleft+shift
            #return self.rect.topright+array([-shift[0],shift[1]])
        return UI_Icon.get_hotspot(self,*args,**kwargs)

class ResIcon(UI_Icon):
    mutable=True
    sound=True
    layer=1
    size=graphic_chart['resicon_size']
    def __init__(self,cast,actor,typ, **kwargs):
        super(ResIcon, self).__init__()
        self.set='idle'
        self.cast=self.parent=cast
        self.type=typ
        self.actor = actor
        self.vals =None

    def make_icon(self,size,bcolor,base,mod,imm):
        size=array(size)
        radius=min(size/2)
        image=pgsurface.Surface(size ,pg.SRCALPHA)
        #pg.draw.circle(image,(255,255,255,255),size/2,radius)
        bgcolor=graphic_chart['window_field_bg_idle']
        if mod:
            if mod<0:
                mod,base=base,base+mod
                color=graphic_chart['text_color_negative']+(255,)
            else :
                mod+=base
                color=graphic_chart['text_color_positive']+(255,)
            image.blit( MatchNodeIcon().make_icon(size,radius,(bgcolor,color),mod-.5),(0,0))
            image.blit( MatchNodeIcon().make_icon(size,radius,((0,0,0,0),bcolor),base-.5),(0,0))
        else:
            image.blit( MatchNodeIcon().make_icon(size,radius,(bgcolor,bcolor),base-.5),(0,0))
        if imm:
            color=graphic_chart['teri_color']
            image.blit( MatchNodeIcon().make_icon(size,radius,((0,0,0,0),color),imm-.5),(0,0))
        return image


    def make_surface(self,*args,**kwargs):
        unsaturated=False
        infos={}
        infos.update(self.actor.dft)
        infos.update(self.cast.handler.get_info(self.actor))
        size=self.size
        base=infos[self.type]
        mod=0
        color=graphic_chart[self.type+'_color']
        if 'effects' in infos:
            for k,e in infos['effects'].iteritems():
                if e[0]==self.type:
                    mod+=e[1]
        if self.type=='terr':
            teri=infos.get('teri',0)
        else:
            teri=0
        if not self.vals or (base,mod,teri)!=self.vals:
            self.vals=(base,mod,teri)

            basesurf=load_icon(self.type,val=base,bonus=mod,unsat=unsaturated,imm=teri)
            if basesurf:
                basesurf=pg.transform.smoothscale(basesurf,2*array((radius,radius)))
                surf=pgsurface.Surface(size ,pg.SRCALPHA)
                surf.fill((0,0,0,0))
                surf.blit(basesurf,center-(radius,radius))
            else:
                surf=self.make_icon(size,color,base,mod,teri)
            return surf#px.make_surface()
        else:
            return self.image

    def color_mod(self,state):
        return graphic_chart.get('icon_'+state+'_color_mod',UI_Icon.color_mod(self,state))
        #return UI_Icon.color_mod(self,state)






class ActorPanel(SidePanel):
    title = 'Actor editor'
    attrs=(
        ('name','input','Name',100,{'charlimit':20}),
        ('color','color','Color',100,{'colors':graphic_chart['player_colors']}),
        #('portrait','menu','Portrait',100,{'type':'input'})
        ('portrait','listsel','Portrait',120,{
            'values': [i for i in olistdir(database['portraits'])
             if os.path.isdir(os.path.join(database['portraits'],i )) ] }),
        )


    def __init__(self,interface,infosource,ref=None,**kwargs):
        if not ref:
            ref=Actor()
        self.ref=ref
        self.infosource=infosource
        self.interface=interface
        for dft in (ref.dft_attr,ref.dft_res):
            for i, j in dft.iteritems():
                self.attrs=self.attrs+((i,'drag',ref.dft_names[i],80,{'minval':0.,'maxval':1.}),)
        self.attrs+=(('prof','inputlist','Proficiencies',120,{'add':True,'menu':{'type':'talent'} }),
            )
        SidePanel.__init__(self,interface,infosource,**kwargs)
        self.update()

    def make(self):
        SidePanel.make(self,cats={'color':self.input})
        #por=self.input['portrait']
        #self.change_method(['portrait','text'],
            #lambda e=por.val:user.ui.input_menu('input',lambda e,f='portrait':self.send_info(f,e),title='Portrait folder:',val=e))

class ActorMatchPanel(ActorPanel):
    title = 'Actor editor'
    attrs=deepcopy(ActorPanel.attrs)
    attrs+=(
        ('control','arrowsel','Controller',100,{'values':('human','AI')}),
        ('react','inputlist','Reactions',200,{'add':True,'menu':{'type':'actreac'}}),
        ('prox','inputlist','Proximity',120,{'menu':{'type':'drag'} } ),
        )

class CastSceneView(View):
    #Wrapper for cast assoiated with sprites in a basecanvas
    name='castview'
    def __init__(self,*args,**kwargs):
        View.__init__(self,*args,**kwargs)
        self.hud={}

    def upd_actor(self,actor):
        return True

    def get_hotspot(self,icon):
        #icon=self.icon[actor]
        shift=(0,0)# array(icon.rect.size)/10
        if icon.rect.center[0]<self.parent.viewport.center[0]:
            return array( icon.rect.topright+array(shift) -(icon.rect.w/3.,0),dtype='int')
        else:
            return array(icon.rect.topleft+array(shift) +(icon.rect.w/3.,0),dtype='int')

    def upd_actors(self):
        [self.upd_actor(actor) for actor in self.handler.actors ]

    def event(self,event,**kwargs):
        return False
        kwargs.setdefault('children',self.icon.values())
        if UI_Widget.event(self,event,**kwargs):
            return True
        return False



class CastView(View):
    name='castview'
    def __init__(self,*args,**kwargs):
        View.__init__(self,*args,**kwargs)
        self.hud={}

    def actor_pos(self,icon,i):
        pos=(i//2)*graphic_chart['cast_spacing']
        pos+=graphic_chart['cast_margin']
        if i%2==0:
            icon.rect.left= pos
            icon.mirrorx=False
        else :
            icon.rect.right= self.parent.rect.width-pos
            icon.mirrorx=True
        hud=self.hud[icon.actor]
        hud.rect.midbottom=icon.rect.center
        hud.rect.bottom=self.parent.rect.bottom
        icon.mutate()
        hud.update()
        #hud.mutate()
        self.pos[icon.actor]=icon.rect.topleft
        self.pos[hud]=icon.rect.topleft


    def get_hotspot(self,icon):
        #icon=self.icon[actor]
        shift=array(icon.rect.size)/10
        if icon.mirrorx:
            return icon.rect.topleft+shift
        return icon.rect.topright+array([-shift[0],shift[1]])

    def upd_actor(self,actor):
        if not actor in self.icon :
            self.add_actor(actor)
            self.upd_actors()
            return
        ids=sorted([a.ID for a in self.icon])
        self.icon[actor].make_faces()
        self.actor_pos(self.icon[actor],ids.index(actor.ID))

    def rem_actor(self,actor):
        self.children.remove(self.icon[actor])
        self.group.remove(self.icon[actor])
        del self.icon[actor]
        self.children.remove(self.hud[actor])
        self.group.remove(self.hud[actor])
        self.hud[actor].kill(1)
        del self.hud[actor]

    def add_actor(self,actor):
        icon=self.icon[actor]=ActorIcon(self,actor)
        self.group.add(icon,layer=0)
        self.children.append(icon)
        icon.parent=self
        hud=self.hud[actor]=self.make_hud(actor)
        #hud.children.append(icon)
        hud.parent=self
        self.group.add(hud,layer=1)
        self.children.append(hud)

    def upd_actors(self):
        [self.upd_actor(actor) for actor in self.handler.actors ]

    def event(self,event,**kwargs):
        kwargs.setdefault('children',self.icon.values())
        if UI_Widget.event(self,event,**kwargs):
            return True
        return False

    def make_hud(self,actor):

        icon=self.icon[actor]
        infos={}
        infos.update(actor.dft)
        infos.update(self.handler.get_info(actor))
        txt=infos['name']
        hudtxt=Emote([txt],font=fonts["charaname"])
        hudtxt.actor=actor
        face=ResIcon(self,actor,'face')
        terr=ResIcon(self,actor,'terr')
        hud=UI_IContainer(size=icon.rect.size,children=[hudtxt,face,terr])
        hud.txt=hudtxt
        hud.actor=actor
        hud.parent=self
        hud.create(self.group)

        cen=array(hud.rect.center)
        tl=hud.rect.bottomleft
        tr=hud.rect.bottomright
        hudtxt.rect.center=cen
        hudtxt.rect.bottom=hud.rect.bottom
        hud.pos[hudtxt]=hudtxt.rect.center
        hud.pos[terr]=tl+(cen-tl)*(.2,.2)
        hud.pos[face]=tr+(cen-tr)*(.2,.2)
        return hud

    def hud_event(self,typ,*args):
        try:
            if not hasattr(args[0],'__iter__'):
                actors=[args[0]]
            else:
                actors=args[0]
            if not set(actors)&set(self.handler.actors):
                actors=self.handler.actors
        except:
            actors=self.handler.actors
        for actor in actors:
            if typ=='hide':
                self.hud[actor].rem_from_group(self.group)
            elif typ=='show':
                self.hud[actor].add_to_group(self.group)
            elif typ=='anim':
                self.hud[actor].set_anim(args[1])

