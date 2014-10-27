# -*- coding: utf-8 -*-
from gv_component import *

#BaseCanvas is the base class for anything that contains multiple icons and multiple plans

class BaseCanvasLayer(DataItem):
    dft={
        'name':'Layer',
        'offset':array((0,0)),
        'state':'idle',
        'distance':0,
        'zoom':1,
        'alpha':1,
        'items':[],
        'pos':{},
        'bound':None, #source of data for items in layer
        'parent':None, #parent layer
        'children':[] #children layers
        }
    states=('idle','hidden','ghost','blur')

    def contains(self,item):
        return item in self.items

    def __init__(self,*args,**kwargs):
        DataItem.__init__(self,*args,**kwargs)
        self.type='layer'

    def __repr__(self):
        return self.name+' '+str(id(self))

    #def set_attr(self,i,j):
        #TOO DANGEROUS! CHANGES IMPOSSIBLE TO UNDO
        #if i=='parent' and j!=self.parent:
            #if hasattr(j,'children') and not self in j.children:
                #j.children.append(self)
        #if i=='children':
            #for c in j:
                #c.parent= self
        #DataItem.set_attr(self,i,j)

class BaseCanvasData(Data):
    #This should be a Data so as to memorize the exact configuration
    #for instance for reload mid-game
    #It also knows if layers refer to other datastructures
    #rather than being purely visual planes (as in cutscenes)
    #In general the items put in layers can be items from other datastructures,
    #or dedicated sprites

    dft={'size':ergonomy['default_canvas_size'],'pan':(0,0),'zoom':1 }
    infotypes={'layer':('offset','state','zoom','distance','items','name','bound','order'),
         }

    multi_belong=False #if True, a given object can belong to multiple layers
    Layer=BaseCanvasLayer

    def __init__(self,**kwargs):
        self.pan=(0,0)
        self.zoom=1
        Data.__init__(self,**kwargs)
        #if not self.layers:
            #self.add(self.Layer())

    def get_layer(self,item):
        if not self.multi_belong:
            for l in self.layers:
                if l.contains(item):
                    return l
        else:
            lays=[]
            for l in self.layers:
                if l.contains(item):
                    lays.append(l)
            return lays
        return False

    def txt_export(self,*args,**kwargs):
        if not 'order' in self.infotypes['layer']:
            self.infotypes['layer']+=('order',)
        for il,l in enumerate(self.layers):
            self.set_info(l,'order',il)
        Data.txt_export(self,*args,**kwargs)

    def txt_import(self,*args,**kwargs):
        Data.txt_import(self,*args,**kwargs)
        for l in tuple(self.layers):
            self.layers.remove(l)
            self.layers.insert(self.get_info(l,'order'),l)

class BaseCanvasIcon(UI_Icon):
    state_list=('idle','hover','select','ghost')
    sound=True
    draggable=True
    bounded=0 #limited to borders of canvas
    hotspot={} #Anchor for bubbles and emotes

    def __init__(self,canvas,item):
        self.item=item
        self.rect=pgrect.Rect((0,0),(1,1))
        self.size=self.rect.size
        super(BaseCanvasIcon, self).__init__()
        #self.priority.update({'hidden':0})
        #self.states.update({'hidden':False})
        if canvas:
            self.canvas=canvas
            self.id=canvas.id
            canvas.id+=1
    def event(self,event,**kwargs):
        return False

    def drag(self,rel):
        rect = self.rect.move(rel)
        bound=self.canvas.rect
        if not self.bounded or bound.contains(rect):
            self.rect.move_ip(rel)
            self.canvas.pos[self.item]=self.canvas.pos[self.item]+array(rel,dtype='int')
        elif not bound.contains(self.rect):
            rel=-array(self.rect.topleft)
            self.rect.clamp_ip(bound)
            rel+=self.rect.topleft
            self.canvas.pos[self.item]=self.canvas.pos[self.item]+array(rel,dtype='int')

    def set_pos(self,pos):
        self.rect.center=pos
        self.canvas.pos[self.item]=array(pos)

    #def set_state(self,state,force_redraw=False,**kwargs):
        #if UI_Icon.set_state(self,state):
            #if state=='hidden':
                #self.canvas.hide(self)
            #return 1
        #return 0

    #def rm_state(self,state,force_redraw=False,**kwargs):
        #if UI_Icon.rm_state(self,state):
            #if state=='hidden':
                #self.canvas.show(self)
            #return 1
        #return 0


class BaseCanvasView(View):
    icon_types={'dft':BaseCanvasIcon}
    bg=None
    BaseCanvasflag=True
    dft_size=(1000,800)
    def __init__(self,handler,parent=None,**kwargs):
        View.__init__(self,handler,parent,**kwargs)
        self.select_opt['auto_unselect']=True  #unselect selected by clicking anywhere else

        size=None
        #self.bg=None
        self.dirty= 1
        self.motion=[]
        self.rect = pg.rect.Rect((0,0),ergonomy['default_canvas_size'])
        self.make()
        for i,j in kwargs.iteritems():
            if i =="surface" or i=="surf" :
                self.surface = j
            if i=='rect' :
                self.rect = j
            if i=='bg':
                self.bg=j
            if i=='data' and j :
                self._data = j
            if i=='size' and j :
                size = j

        self.offset=(0,0)
        if not size :
            if parent:
                size=parent.screen.get_rect().size
            else:
                size=self.dft_size
        self.viewport=pgrect.Rect((0,0),size)

        if not hasattr(self,'surface'):
            self.surface = pgsurface.Surface(self.rect.size,self.BaseCanvasflag)
            self.surface.set_colorkey(COLORKEY)
        #self.veil=None
        self.surface.fill(COLORKEY)
        if handler :
            self.set_handler(handler)
        self.mask=pg.mask.from_surface(self.surface)

    def set_handler(self,handler):
        self.handler=handler

    @property
    def data(self):
        if self.handler:
            return self.handler.data
        return self._data

    def make(self):
        self.id=0
        self.items={}
        #self.blocks={}#Unused for now
        #wid,hei = ergonomy['canvas_block_size']
        #for i in range(self.rect.w//wid +1 ):
            #for j in range(self.rect.h//hei +1 ):
                #self.blocks[(i,j)] =pgsprite.LayeredUpdates()
        self.group=pgsprite.LayeredUpdates()
        self.tools=pgsprite.Group()
        self.animated=pgsprite.Group()
        self.pos={}
        self.icon={}
        self.layers=[]

    def order_layers(self):
        for nl,l in enumerate(self.data.layers):
            for i in l.items:
                if i in self.icon:
                    self.group.change_layer(self.icon[i],nl)

    def icon_update(self,target):
        icon=self.icon[target]
        icon.create(self.group,'all')
        self.group.change_layer(icon,self.data.layers.index(self.data.get_layer(icon.item)))
        self.assess_itemstate(target)

    def update(self,*args):
        #self.surface.fill(COLORKEY)
        if self.animated :
            self.animated.update()
        if self.dirty:
            if self.handler.clickable:
                surface=self.surface#.copy()
                surface.fill(COLORKEY)
                for s in self.group:
            #if s.rect.colliderect(self.handler.viewport.rect.move(self.handler.viewport.offset)):
                    surface.blit(s.image,self.pos[s.item]-array(s.rect.size)/2)
                if not user.grabbed:
                    self.mask=pg.mask.from_surface(surface)
            #else:
                #self.mask=pg.mask.from_surface(self.surface)
                #self.mask.clear()
            self.dirty=0


    def paint(self,surface=None):
        if not surface:
            surface=self.surface
            if not self.bg:
                self.surface.fill(COLORKEY)

        offset=self.offset
        viewrect=self.viewport.move(offset)
        offset=-array((offset[0],offset[1]))
        if self.bg :
            surface.blit(self.bg,offset)
        relzoom=1.
        reloffset=0.
        w,h=surface.get_rect().size
        for c in self.children:
            if hasattr(c,'paint'):
                c.paint(surface)
        #if hasattr(self,'veil') and self.veil:
            #surface.blit(self.veil,(0,0),None,pg.BLEND_RGBA_MULT )
        self.group.draw(surface)

        return
        #for l in self.data.layers:
            #inf=self.data.get_info(l)
            #loffset,zoom=array(inf['offset']),inf['zoom']
            #for i in l.items:
                #s=self.icon[i]
                #locrect=array(l.pos[i],dtype='int') *zoom + loffset
                #self.pos[i]=locrect
                #locsize= array(s.rect.size,dtype='int')*zoom
                #if pg.Rect(locrect,locsize).colliderect(viewrect) and not s.states['hidden']:
                    #if zoom!=s.zoom:
                        #s.zoom=zoom
                        #s.mutate()
                    #surface.blit(s.image,locrect+offset-array(s.rect.size)/2)
        #self.mask=pg.mask.from_surface(surface)

    def upd_pos(self):
        for i in self.icon:
            s=self.icon[i]
            s.rect.topleft=self.pos[i]-array(s.rect.size)/2-self.offset
        self.dirty=1

    def upd_layer(self,l=None):

        if l is None:
            for i in self.data.layers:
                self.upd_layer(i)
            return
        viewrect=self.viewport.move(self.offset)
        inf=self.data.get_info(l)
        loffset,zoom=array(inf['offset']),inf['zoom']
        for i in l.items:
            s=self.icon[i]
            locrect=array(l.pos[i],dtype='int') *zoom + loffset
            self.pos[i]=locrect
            s.rect.topleft=self.pos[i]-array(s.rect.size)/2-self.offset
            locsize= array(s.rect.size,dtype='int')*zoom
            if pg.Rect(locrect,locsize).colliderect(viewrect):
                if zoom!=s.zoom:
                    s.zoom=zoom
                    s.mutate()
                #surface.blit(s.image,locrect+offset-array(s.rect.size)/2)
        self.dirty=1

    def assess_itemstate(self,items=None):
        self.handler.catch_new()
        if items is None:
            items=self.icon.keys()
        elif items and not hasattr(items,'__iter__'):
            items = [items]
        elif not items:
            return False
        states={l:self.data.get_info(l,'state') for l in self.data.layers}
        for item in items:
            if not item in self.icon:
                continue
            state= states[self.data.get_layer(item)]
            icon=self.icon[item]
            if state=='hidden':
                self.group.remove(icon)
                self.animated.remove(icon)
            elif state in icon.state_list:
                icon.set_state(state)
            else:
                icon.set_state('idle')
        self.upd_layer()

    def test_hovering(self,event,**kwargs):
        if 'pos' in kwargs:
            pos=kwargs['pos']
        else:
            refpos=kwargs.get('refpos',(0,0))
            if refpos!=(0,0) and hasattr(event,'pos') :
                pos=event.pos
                pos = tuple(array(pos)-array(refpos))
            else :
                pos=self.mousepos()
        layer=kwargs.get('layer',self.handler.active_layer)
        linfo=self.handler.data.get_info(layer)
        pos=array(pos)#-linfo['offset']
        user.setpos(pos-array(self.offset))
        hover = None
        try:
            self.mask.get_at(pos)
        except:
            return hover
        if self.mask.get_at(pos) :
            #try :
                #hover=pgsprite.spritecollide(user.arrow,
                    #[n for n in self.group if hasattr(n,'radius')] ,
                    #False,pgsprite.collide_circle)[-1]
            #except :
            try :
                #print self.handler.active_layer.items, self.handler.active_layer
                ics=[self.icon[i] for i in layer.items]
                prelim=pgsprite.spritecollide(user.arrow,
                    [l for  l in ics if l in self.group],False)
                while hover == None :
                    test = prelim.pop()
                    if pgsprite.collide_mask(user.arrow,test):
                        hover = test
                #hover=pgsprite.spritecollide(user.arrow,canvas.links,False,pgsprite.collide_mask)[-1]'''
                #hover=prelim[-1]
            except:
                pass
            if not hover:
                tmp=pgsprite.spritecollide(user.arrow,
                    [t for t in self.tools if t in self.group] ,
                    False,pgsprite.collide_circle)
                if tmp:
                    self.hover(tmp[-1])
                    return tmp[-1].event(event,**kwargs)

            if hover and not hover.is_ghost :
                self.hover(hover)
            else :
                self.unhover()
        return hover

    def event(self,event,**kwargs):
        if View.event(self,event,**kwargs):
            return True
        #if event.type==29:#pg.USEREVENT  :
            #self.veil=pg.surface.Surface(user.ui.screen.get_rect().size )
            #self.veil.fill( (255,255,255,255))
            #self.aboriginize(self.veil)
            ##VEIL TO CHANGE
            #if not self.veil:
                #self.veil=pgsurface.Surface(self.rect.size).convert()
                #self.veil.fill((100,100,100,100) )
            #t1= pg.time.get_ticks()
            #self.veil.fill((0,0,0 ) )
            #w,h=self.veil.get_rect().size
            #for l in range(1500):
                #pg.draw.circle(self.veil,(55,55,55),(rnd.randint(0,w),
                    #rnd.randint(0,h) ),rnd.randint(5,20) )
            #print pg.time.get_ticks()-t1
        if event.type==30 and self.motion:
            m=self.motion[0]
            dist=array(m)-self.offset
            step=int( ergonomy['canvas_glide_speed']*1./ergonomy['animation_fps'])
            hyp=hypot(*dist)

            if hyp < step*1.5:
                self.set_offset(m,False)
                self.motion.pop(0)
            else :
                rel=hyp/ergonomy['canvas_typical_dist']
                if rel>1:
                    step=rint(step* (rel) )
                rad,angle=hypot(*dist),atan2(dist[1],dist[0])
                oldoff=self.offset
                self.set_offset( (int(step*cos(angle)),int(step*sin(angle)) ))
                if oldoff==self.offset: #blocked by boundaries)
                    self.motion.pop(0)

        try:
            if self.block_actions:
                return False
        except:
            pass
        handled=False
        refpos=kwargs.get('refpos',(0,0))
        if refpos!=(0,0) and hasattr(event,'pos') :
            pos=event.pos
            pos = tuple(array(pos)-array(refpos))
        else :
            pos=self.mousepos()

        if not self.rect.collidepoint(pos):
            self.handler.drop()
            return False
        if not self.mask.get_at(pos) and user.state == 'idle' and not event.type in (pg.MOUSEBUTTONDOWN,pg.MOUSEBUTTONUP ):
            handled=handled or self.handler.bgpoint()
            if not event.type==pg.MOUSEMOTION or not pg.mouse.get_pressed()[0]:
                self.unhover()
                return handled
            else :
                self.motion=[]
                return self.handler.bgdrag(array(event.rel))

        if user.state=='grab' and event.type == pg.MOUSEMOTION :
            if pg.mouse.get_pressed()[0] :
                rel=event.rel
                foc=user.grabbed
                if self.handler.sticky:
                    rate=ergonomy['nodes_stickyness_to_mouse']
                    rel+=(array(pos)-self.pos[foc] +array(foc.rect.size)/2)*rate
                    rel=array(rel,dtype='int')
                rect =foc.drag(rel)
            else :
                self.handler.drop()
            return True

        if user.state == 'idle'  and event.type in (pg.MOUSEBUTTONDOWN,pg.MOUSEBUTTONUP,pg.MOUSEMOTION) :
            hover=self.test_hovering(event,pos=pos)
            if event.type == pg.MOUSEBUTTONDOWN :
                if not hover and self.select_opt['auto_unselect'] :
                    self.unselect()
                if event.button ==1 :
                    handled=self.handler.left_click(hover,event)
                elif event.button==3 :
                    handled = self.handler.right_click(hover,event)
                elif event.button>3:
                    handled=self.handler.mousewheel(hover,event)
            elif hover and  event.type == pg.MOUSEMOTION and  pg.mouse.get_pressed()[0]:
                self.handler.drag()
        if not handled :
            if event.type == pg.MOUSEBUTTONUP :
                self.handler.drop()
                handled = True
        if handled :
            self.dirty=True
        return handled

    def set_offset(self,offset,additive=True):
        if additive:
            offset=array(offset)
            ioff =array(self.offset)
            offset=tuple(ioff+offset)
        rect=pgrect.Rect(offset,self.viewport.size).clamp(self.rect)
        if rect.topleft != self.offset :
            self.offset=rect.topleft
            self.upd_pos()
            return True
        return False

    def hide(self,icon):
        self.group.remove(icon)
    def show(self,icon):
        self.group.add(icon,layer=self.data.get_layer(icon.item) )

class BaseCanvasHandler(Handler):
    name='canvas'
    dft_layer_states={'idle':'ghost'}
    active_layer=None
    View=BaseCanvasView
    Data=BaseCanvasData
    sticky=0 #stick object center to mouse
    clickable=1 #click activity on canvas objects (i.e. not a static scene)

    def __init__(self,parent,**kwargs):
        Handler.__init__(self,parent,**kwargs)
        self.dft_layer_states=deepcopy(BaseCanvasHandler.dft_layer_states)
        if not self.data.layers:
            self.data.add(self.data.Layer() )
        self.set_layer(self.data.layers[0])
        self.view.rect = pg.rect.Rect((0,0),self.data.size)
        self.make_icons()
        if self.data.bg:
            self.set_background(self.data.bg)

    def set_background(self,bg):
        if bg=='None':
            self.view.bg=None
            self.data.bg=None
            return
        try:
            self.view.bg=image_load(bg).convert()
        except:
            self.view.bg=image_load(database['backgrounds']+bg).convert()
            try:
                 if (self.view.bg.get_size()<self.view.surface.get_size()).any():
                     self.view.bg=pg.transform.smoothscale(self.view.bg, self.view.surface.get_size())
            except:
                pass
        self.view.bg=pg.transform.smoothscale(self.view.bg,user.screen.get_rect().size )
        self.data.bg=bg


    @property
    def layers(self):
        return self.data.layers


    def make_dependencies(self,transmit_upward=False):
        self.depend.clear()
        self.depend.add_dep(self,self.data)
        for l in self.layers:
            self.depend.add_dep(self,l)
        if transmit_upward:
            try:
                self.parent.make_dependencies()
            except:
                pass

    def make_icons(self):
        for l in self.data.layers:
            for i in l.items:
                kwargs=self.data.get_info(i)
                if i in l.pos and (not i in self.view.pos or l==self.active_layer):
                    kwargs['pos']=l.pos[i]
                kwargs.setdefault('layer',l)
                self.add(i,**kwargs)
        self.view.assess_itemstate()

    def pan(self,rel):
        evt=PanEvt(self.data,rel)
        evt.prep_init()
        evt.state=1
        user.evt.go(evt,2,ephemeral=1)
        #for l in self.layers:
            #offset=tuple(int(i*(1.-self.data.get_info(l,'distance'))) for i in rel)
            #user.evt.do(ChangeInfosEvt(l,self.data,offset=array(offset),additive=1),self)


    def set_data(self,data):
        Handler.set_data(self,data)
        self.set_layer(self.data.layers[0])
        self.view.make()
        self.view.rect = pg.rect.Rect((0,0),self.data.size)
        self.make_icons()
        self.view.order_layers()
        if self.data.bg:
            self.set_background(self.data.bg)
        self.view.update()


    def label(self,item,state=None):
        return item.type.capitalize()+' '+str(getattr(self.data,item.type+'s').index(item))+': '+item.name

    def change_infos(self,target,**kwargs):
        eph=kwargs.pop('invisible',False)
        datasrc=kwargs.pop('data',self.data.get_info(self.active_layer,'bound') )
        if not datasrc:
            print 'ERROR Basecanvas change_infos: No data'
            return 0
        evt=ChangeInfosEvt(target,datasrc,**kwargs)
        return  user.evt.do(evt,self,ephemeral=eph)
        #if user.evt.do(evt,self,ephemeral=eph):
            #self.react(evt)
            ##if self.handler :
            ##    self.handler.signal('info_change',target,**kwargs)
            #return True
        #else :
            #return False

    def left_click(self,target,event=None):
        if not target or not target.item in self.active_layer.items:
            return False
        if target == user.just_clicked :
            user.just_clicked=None
            return self.double_click(target)
        else :
            pg.time.set_timer(31,ergonomy['double_click_interval'])#just clicked remover
            user.just_clicked=target

        pg.time.delay(40)
        evts= pgevent.get((pg.MOUSEMOTION,pg.MOUSEBUTTONUP,pg.MOUSEBUTTONDOWN))
        if not evts or evts[0].type==pg.MOUSEBUTTONUP:
            self.view.select(self.view.hovering)
            user.state='idle'
            return True
        else :
            newevent=evts[0]
        if newevent.type == pg.MOUSEMOTION:
            return self.drag()
        elif newevent.type == pg.MOUSEBUTTONDOWN :
            # Impossible for a human in such a short delay, but catch it anyway
            return self.double_click(target)
        return self.event(newevent)

    def double_click(self,target, event=None):
        return True

    def right_click(self,target,event=None):
        return False

    def select(self,item):
        evt=SelectEvt(item,affects=[self.data,self],source=self.name)
        return user.evt.do(evt,ephemeral=True)

    def mousewheel(self,target,event):
        if event.button==4:
            d=1
        elif event.button==5:
            d=-1
        return False

    def bgdrag(self,rel):
        self.view.set_offset(-rel)

    def drag(self):
        hover=self.view.hovering
        if  hover and hover.draggable and hover.item in self.active_layer.items:
            user.state='grab'
            user.grab(hover)
            return True
        return False

    def drop(self):
        grabbed= user.grabbed
        if user.ungrab():
            user.state ='idle'
            if grabbed==self.view:
                #For some cases of bg drag, when I want to update the view but not the mask
                return
            grabbed=grabbed.item
            inf= self.data.get_info(self.active_layer)
            pos=array((array(self.view.pos[grabbed])-inf['offset'])/inf['zoom'],dtype='int')
            evt=MoveEvt(grabbed, self.active_layer,pos,affects=(self.data,))
            if user.evt.do(evt,self):
                self.view.dirty=True


    def react(self,evt):
        if 'move' in evt.type:
            inf= self.data.get_info(self.active_layer)
            self.view.icon[evt.item].set_pos(array(evt.graph.pos[evt.item])*inf['zoom']+inf['offset'])
            self.view.icon_update(evt.item)
            self.view.upd_pos()
            self.view.dirty=True
        if 'pan' in evt.type or 'zoom' in evt.type:
            for l in self.layers:
                self.view.upd_layer(l)
        if 'change_infos' in evt.type and evt.item==self.data:
            if 'bg' in evt.infos :
                self.set_background(self.data.bg)
            if 'size' in evt.infos:
                self.view.rect = pg.rect.Rect((0,0),self.data.size)
        if 'change_infos' in evt.type  and evt.item in self.data.infos  :
            item=evt.item
            if array( [i in evt.infos for i in ('val','genre','set') ]).any():
                self.view.icon_update(item)
            if 'offset' in evt.infos or 'zoom' in evt.infos:
                self.view.upd_layer(evt.item)
            if 'state' in evt.infos:
                state= evt.kwargs.get('state',None)
                if state == 'hidden' and evt.state==1:
                        [ self.view.hide(self.view.icon[s]) for s in evt.item.items ]
                else:
                        [ self.view.show(self.view.icon[s]) for s in evt.item.items ]
                if state == 'ghost' and evt.state==1:
                        [self.view.icon[s].set_state('ghost') for s in evt.item.items ]
                else:
                        [self.view.icon[s].rm_state('ghost')  for s in evt.item.items ]
        if ('add' in evt.type or 'rem' in evt.type)  and evt.item in self.data.infos :
            item=None
            if 'layer' in evt.item.type:
                self.set_layer(evt.item,len(self.layers))
            elif 'sprite' in evt.item.type :
                item= evt.item
                layer= evt.infos.get('layer',evt.data)
                if evt.state==1:
                    self.add(item,layer=layer,**evt.kwargs)
                elif evt.state==0:
                    layers=(evt.data,)+tuple(evt.data.children)
                    if self.data in layers:
                        layers=self.layers
                    self.remove(item,layers,**evt.kwargs)
        if evt.kwargs.get('assess',False) :
            self.view.assess_itemstate(item)
        if evt.kwargs.get('update',False) :
            self.update()
        for c in evt.states.node[evt.state]['children_states']:
            if c.state == evt.states.node[evt.state]['children_states'][c]:
                #react to it only if the child event has really been executed!
                self.react(c)
        return Handler.react(self,evt)


    def get_info(self,item,info=None,**kwargs):
        if hasattr(item,'item'):
            item=item.item
        return self.data.get_info(item,info,**kwargs)



    def get_infotypes(self,typ):
        return self.data.get_infotypes(typ)


    def set_layer(self,layer=None,pos=0,**kwargs):
        if hasattr(layer,'__iter__'):
            for g in layer[::-1]:
                try :
                    self.layers.remove(g)
                except :
                    pass
                self.layers.insert(pos,g)
        else :
            if not layer :
                if len(self.layers)==1 :
                    return False
                layer = self.layers[-1]
            try :
                self.layers.remove(layer)
            except :
                pass
            self.layers.insert(pos,layer)
        #for l in self.layers[1:]:
            #self.state[l]=self.dft_layer_states.get(l,self.dft_layer_states['idle'])

        if kwargs.get('activate',1):
            layer = self.layers[0]
            self.set_active_layer(layer)
        #print debug.caller_name()
        #print self.layers, self.state
        if kwargs.get('signal',True):
            self.signal('set_layer',layer)
        #self.assess_itemstate()
        self.view.order_layers()
        return True


    def set_active_layer(self,layer,**kwargs):
        prev= self.active_layer
        if layer == prev :
            return False
        self.active_layer=layer
        #self.state[layer]='active'
        #self.state[prev]=self.dft_layer_states.get(prev,self.dft_layer_states['idle'])
        self.view.order_layers()
        if kwargs.get('signal',True):
            self.signal('set_active_layer',layer)
        return True

    def catch_new(self):
        """If new items have been added to some layer, add them."""
        for l in self.layers :
            new_items=[x for x in self.data.new_items if x in l.items]
            src=self.data.get_info(self.active_layer,'bound')
            if src:
                new_items+=src.new_items
            for item in tuple(new_items):
                #print item, l
                if l == self.data :
                    self.add(item)
                else :
                    self.add(item,layer=l)
                try:
                    src.new_items.remove(item)
                except:
                    self.data.new_items.remove(item)
        return True


    def add(self,item,**kwargs):
        layer=kwargs.get('layer',None)
        if not layer:
            layer=self.active_layer
        view=self.view
        if item in view.icon :
            if  not layer in view.icon[item].image_sets:
                view.icon[item].create(None,layer)
        else :
            args=[]
            if hasattr(item,'parents'):
                picon=[]
                for p in item.parents:
                    picon.append(view.icon[p])
                args.append(picon)
            icon=view.icon_types.get(item.type,view.icon_types['dft'])(view,item,*args)
            icon.parent=view
            offset=array(self.data.get_info(layer,'offset') )
            zoom=self.data.get_info(layer,'zoom')
            handled=0
            if hasattr(layer,'pos') and item in layer.pos:
                view.pos[item]=layer.pos[item]*zoom+offset
                handled=1
            for i,j in kwargs.iteritems():
                if i=='pos':
                    view.pos[item]=j
                if i=='state' :
                    icon.set_state(j)
            icon.rect.center=view.pos[item]
            if item in view.pos and not handled:
                layer.pos[item]=(array(view.pos[item])-offset)/zoom
            icon.rect.clamp_ip(view.rect)
            icon.create(view.group,layer)
            view.group.change_layer(icon,self.data.layers.index(layer))
            view.items[icon.id]=icon
            view.icon[item]=icon
        if not self.data.multi_belong:
            if not 'layer' in self.data.infotypes[item.type]:
                 self.data.infotypes[item.type] += ('layer',)
            self.data.set_info(item,'layer',layer)
        else:
            print 'Not tested yet'
            if not self.data.get_info(item,'layer'):
                self.data.set_info(item,'layer',[layer])
            else:
                self.data.set_info(item,'layer',[layer],update=True)
        src=self.data.get_info(layer,'bound')
        if src and item in src.new_items :
            src.new_items.remove(item)
        if not item in layer.items:
            layer.items.append(item)

    def switch_layer(self,item,layer=None):
        oldlayer=self.data.get_info(item,'layer')
        if not layer:
            sdl=self.data.layers
            if oldlayer:
                layer=sdl[(sdl.index(oldlayer) +1)%len(sdl) ]
            else:
                layer=sdl[0]
        if oldlayer:
            self.remove(item,[oldlayer] )
        self.add(item,layer=layer)

    def remove (self,item,layers,**kwargs):
        #remove
        view=self.view
        allayers=[l for l in self.layers if l.contains(item)]
        if set(allayers).issubset(set(layers) ):
            icon = view.icon.pop(item,None)
            if icon :
                del view.items[icon.id]
                icon.kill()
        else:
            icon = view.icon.get(item,None)
            if icon :
                [icon.delete_set(l) for l in layers]
        for l in layers:
            try:
                l.items.remove(item)
            except:
                pass

    def menu(self,event=None,**kwargs):
        return ()

    def event(self,event,**kwargs):
        if event.type==pg.KEYDOWN:
            if self.keymap(event):
                return True
        return super(BaseCanvasHandler,self).event(event)

    def keymap(self,event,**kwargs):
        return False

    def bgpoint(self):
        return False

class BaseCanvasEditor(BaseCanvasHandler):

    def menu(self,event=None,**kwargs):
        target=self.view.hovering
        try:
            typ=target.item.type
        except:
            typ='bg'
        if typ!='bg':
            return self.spritemenu(target.item)
        else:
            return self.bgmenu()
        return struct

    def spritemenu(self,sprite,**kwargs):
        struct=()
        if not ergonomy['edit_on_select']:
            struct+=( ('Edit',lambda t=sprite: self.signal('edit',t)), )
        lays= tuple( (self.data.get_info(l,'name'),lambda t=sprite,lay=l: self.switch_layer(t,lay))
             for l in self.data.layers)
        struct+=(
                ('Delete',lambda t=sprite: self.signal('delete',t)),
                ('Switch layer',lambda ls=lays:self.parent.float_menu(ls) ),
             )
        return struct

    def add_layer(self,layer=None,**kwargs):
        if layer in self.data.layers:
            return 0
        if layer is None:
            layer= self.data.Layer()
            self.depend.add_dep(self,layer)
        return user.evt.do(AddEvt(layer,self.data,**kwargs))

    def bgmenu(self,*args,**kwargs):
        struct=()
        if not user.ui.view['layermenu'] :
            struct+=('Edit layers',lambda t=self: self.signal('layermenu',t) ),
        return struct

    def keymap(self,event,**kwargs):
        handled=False
        if event.key==pg.K_TAB :
            llen=len(self.layers)
            if llen>1:
                self.set_active_layer(self.layers[(self.layers.index(self.active_layer)+1)%llen] )
            handled=True
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_PAGEUP:
                llen=len(self.layers)
                self.set_layer(self.active_layer,min(self.layers.index(self.active_layer)+1,llen) ,activate=False)
                handled=True
            elif event.key==pg.K_PAGEDOWN:
                self.set_layer(self.active_layer,max(self.layers.index(self.active_layer)-1,0) ,activate=False)
                handled=True

        if event.key in (pg.K_UP,pg.K_DOWN,pg.K_LEFT,pg.K_RIGHT):
            if event.key==pg.K_UP:
                dif=(0,-10)
            elif event.key==pg.K_DOWN:
                dif=(0,10)
            elif event.key==pg.K_RIGHT:
                dif=(10,0)
            elif event.key==pg.K_LEFT:
                dif=(-10,0)
            if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
                self.pan(dif)
            else:
                self.view.set_offset(dif)
            handled=1
        return handled or BaseCanvasHandler.keymap(self,event)

    def bgpoint(self):
        #user.set_status( 'Layer '+str(self.layers.index(self.active_layer)) )
        return False

