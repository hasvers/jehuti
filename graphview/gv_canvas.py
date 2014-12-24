from gv_ui_complete import *
from gv_canvasicons import *
from gv_graph import *


class Canvas():
    dft_size=(100,100)
    graph_states=('active','ghost','hidden')
    dft_graph_states={'idle':'ghost'}
    name='canvas'
    Graph=Graph
    NodeIcon=NodeIcon
    LinkIcon=LinkIcon

    def __init__(self,**kwargs):
        self.bg=None
        self.dirty= False
        self.motion=[]
        self.rect = pg.rect.Rect((0,0),ergonomy['default_canvas_size'])
        self.handler=handler=None
        self.make()
        self.dft_graph_states=deepcopy(Canvas.dft_graph_states)
        graph= self.Graph()
        for i,j in kwargs.iteritems():
            if i =="surface" or i=="surf" :
                self.surface = j
            if i=='rect' :
                self.rect = j
            if i=='handler':
                handler = j
            if i=='bg':
                self.bg=j
            if i=='graph' and j :
                graph = j

        if not hasattr(self,'surface'):
            self.surface = pgsurface.Surface(self.rect.size,Canvasflag)
            self.surface.set_colorkey(COLORKEY)
        self.surface.fill(COLORKEY)
        self.static_surface=self.surface.convert_alpha()
        if handler :
            self.set_handler(handler)

        self.set_graph(graph)

    def make(self):
        self.id=0
        self.items={}
        self.blocks={}#Unused for now
        wid,hei = ergonomy['canvas_block_size']
        for i in range(self.rect.w//wid +1 ):
            for j in range(self.rect.h//hei +1 ):
                self.blocks[(i,j)] =pgsprite.LayeredUpdates()
        self.group=pgsprite.LayeredUpdates()
        self.nodes=pgsprite.Group()
        self.links=pgsprite.Group()
        self.tools=pgsprite.Group()
        self.animated=pgsprite.Group()
        self.pos={}
        self.icon={}

    def abspos(self,icon):
        #NB: contrary to windows, here pos contains the CENTER
        if not icon:
            return array((0,0))
        if icon.item in self.pos:
            return self.pos[icon.item]+array(icon.rect.topleft)-icon.rect.center
        else:
            return icon.rect.topleft

    def set_handler(self,handler):
        self.handler=handler
        if self.bg :
            self.handler.bg=pg.transform.smoothscale(self.bg,self.rect.size)
        #self.handler.signal('set_handler')


    def set_graph(self,graph):
        self.make()
        self.graph=graph
        self.active_graph = graph
        self.state={graph:'active'}
        self.layers=[graph]+graph.children

#        self.allicons={graph:{}}
#        for c in graph.children:
#            self.allicons[c]={}
        ns=graphic_chart['node_base_size']


        for n in graph.nodes :
            if hasattr(graph,'pos') and n in graph.pos :
                pos = graph.pos[n]
            else :
                pos=(rnd.randint(ns,self.rect.w-ns),rnd.randint(ns,self.rect.h-ns))
            self.add(n,pos=pos,rule='None')

        for p,l in graph.links.iteritems() :
            for link in l :
                self.add(link,rule ='None')

        for c in graph.children :
            for item in c.infos.keys():
                self.add(item,layer=c)

        self.set_layer(graph,0)

        self.update()
        if self.handler :
            self.handler.signal('set_graph')
            self.handler.make_dependencies()
        return True

    def set_graph_from_file(self,filename):
        print 'Set graph from', filename
        if not database['graph_ext'] in filename:
            fin = fopen(database['graph_path']+filename+database['graph_ext'], "rb" )
        else :
            fin = fopen(filename, "rb")
        graph = pickle.load( fin)
        fin.close()
        if not hasattr(graph,'nodes'):
            raise Exception('Not a valid graph file')
            return False
        else :
            return self.set_graph(graph)
        #except :
         #   raise Exception('Not a valid graph file')
          #  return False

    def save_graph_to_file(self,filename):
        print 'Saving graph as',filename
        if not database['graph_ext'] in filename:
            fout = fopen(database['graph_path']+filename+database['graph_ext'], "wb" )
        else :
            fout = fopen(filename, "wb" )

        self.graph.pos=self.pos

        self.handler.signal('save_graph')
        pickle.dump( self.graph,fout  )
        fout.close()

    def new_graph(self,*args):
        graph=self.graph
        graph.make(*args)
        self.set_graph(graph)

    def add(self,item,**kwargs):
        ''' Add item to the fundamental graph or to a specified layer
        and create its icon(s) for said layer.
        NB: By default, any item added to the main graph is transferred
        to its subgraphs according to their selection rules.'''

        ## After refactoring into event, this should be used only for
        # non-data objects such as linkgrabber or beacon, and
        # graph loading or other internal procedures

        if kwargs.get('addrequired',False):
            for i in item.required:
                self.add(i,**kwargs)

        layer = kwargs.pop('layer',False)

        if not layer :
            if not self.graph.add(item,**kwargs) :
                if item in self.icon :
                    return False
            icon=kwargs.pop('icon',False)
            if icon:
                pass
            elif item.type=='node':
                icon = self.NodeIcon(self,item)
            elif item.type =='link':
                picon=[]
                icon = self.LinkIcon(self,item,picon)
                for p in item.parents:
                    if not p in self.icon :
                        self.add(p)
                    picon.append(self.icon[p])
                    picon[-1].ilinks.append(icon)
                icon.parents=tuple(picon)
            elif isinstance(item,LinkGrabber):
                self.icon[item]=item
                return True
            elif isinstance(item,Signal):
                icon=SignalBeacon(self,item)
            else :
                return False
            icon.parent=self
            icon.create(self.group,self.graph)
            self.items[icon.id]=icon
            for i,j in kwargs.iteritems():
                if i=='pos':
                    self.pos[item]=j
                if i=='state' :
                    icon.set_state(j)
            if item in self.pos :
                    icon.rect.center=self.pos[item]
            icon.rect.clamp_ip(self.rect)
            #wid,hei = ergonomy['canvas_block_size']
            if not item in self.icon :
                self.icon[item]=icon

            layer = self.graph
        else :
            if item in self.icon :
                layer.add(item, **kwargs)
                self.icon[item].create(None,layer)
        if item in layer.new_items :
            layer.new_items.remove(item)

        if kwargs.get('assess',False) :
            self.assess_itemstate(item)
        if kwargs.get('update',False) :
            self.update()


        self.dirty = True
        return True

    def remove(self,item,**kwargs):
        '''Remove item either from all layers, or from a specified set.
        Options :
            layer,layers : define
            assess : check state of all items
            update : redraw graph '''
        layers = self.layers
        for i,j in kwargs.iteritems() :
            if i=='layer':
                layers = (j,)
            if i == 'layers':
                layers = j
        for l in layers :
            if item in l.links :
                [self.remove(link,**kwargs) for link in tuple(l.links[item])]
            l.remove(item)
            if l==self.graph :
                icon = self.icon.pop(item,None)
                if icon :
                    del self.items[icon.id]
                    icon.kill()
            else :
                icon = self.icon.get(item,None)
                if icon :
                    icon.delete_set(l)
        if kwargs.get('assess',False) :
            self.assess_itemstate(item)
        if kwargs.get('update',True) :
            self.update()
        self.dirty= True

    def set_ghost(self,item,mode='trigger'):
        icon =self.icon.get(item,None)
        if not icon : return False
        if icon.is_ghost :
            if mode == 'hide':
                return False
            icon.rm_state('ghost')
        else :
            if mode == 'show':
                return False
            icon.set_state('ghost')
        self.dirty=True
        return True

    def set_view(self,item,mode='trigger'):
        """Makes an icon visible or hidden."""
        icon =self.icon.get(item,None)
        if not icon : return False
        if icon not in self.group :
            if mode == 'hide':
                return False
            icon.add_to_group(self.group)
        else :
            if mode == 'show':
                return False
            icon.rem_from_group(self.group)
        self.dirty=True
        return True


    def rewire(self,link,newparents):
        self.graph.rewire(link,newparents)
        icon =self.icon[link]
        picon=[]
        for p in link.parents:
            if not p in self.icon :
                self.add(p)
            picon.append(self.icon[p])
            picon[-1].ilinks.append(icon)
        icon.parents=tuple(picon)

    def change_infos(self,target,**kwargs):
        eph=kwargs.pop('invisible',False)
        evt=ChangeInfosEvt(target,kwargs.pop('graph',self.active_graph),**kwargs)
        if user.evt.do(evt,self,ephemeral=eph):
            self.react(evt)
            #if self.handler :
            #    self.handler.signal('info_change',target,**kwargs)
            return True
        else :
            return False

    def react(self,evt):
        if 'anim' in evt.type:
            anim=evt.args[0]
            item=anim.item
            if evt.type=='anim_start':
                [c.add_to_group(self.animated) for c in [item]+item.children]
            if evt.type=='anim_stop':
                [c.rem_from_group(self.animated) for c in [item]+item.children]
                self.dirty=1
            return
        if 'select' in evt.type :
            if hasattr(evt,'item') and evt.item in self.icon:
                #if not hasattr item, it is a signal, not a SelectEvt, so it should be disregarded
                icon=self.icon[evt.item]
                if evt.state==1 and not icon.is_selected:
                    UI_Widget.select(self.handler,icon)
                    return True
                if evt.state==0 and icon.is_selected:
                    UI_Widget.unselect(self.handler,icon)

        if 'move' in evt.type:
            self.icon[evt.item].set_pos(evt.graph.pos[evt.item])
            #self.icon_update(evt.item)
            self.icon[evt.item].update()
            self.dirty=True
        if 'change_infos' in evt.type:
            if array( [i in evt.infos for i in ('val','genre') ]).any():
                target=evt.item
                self.icon_update(target)
        if 'add' in evt.type or 'rem' in evt.type:
            item= evt.item
            layer= evt.data
            if evt.state==1:
                #print 'Adding', item, "to", layer
                #add
                if item in self.icon :
                    if  layer in self.layers and not layer in self.icon[item].image_sets:
                        self.icon[item].create(None,layer)
                else :
                    if item.type=='node':
                        icon = self.NodeIcon(self,item)
                    elif item.type =='link':
                        picon=[]
                        icon = self.LinkIcon(self,item,picon)
                        for p in item.parents:
    #                        if not p in self.icon :
     #                           self.add(p)
                            picon.append(self.icon[p])
                            picon[-1].ilinks.append(icon)
                        icon.parents=tuple(picon)
                    icon.parent=self
                    if hasattr(layer,'pos') and item in layer.pos:
                        self.pos[item]=layer.pos[item]

                    for i,j in evt.kwargs.iteritems():
                        if i=='pos':
                            self.pos[item]=j
                        if i=='state' :
                            icon.set_state(j)
                    if item in self.pos :
                            icon.rect.center=self.pos[item]
                    icon.rect.clamp_ip(self.rect)
                    icon.create(self.group,layer)
                    self.items[icon.id]=icon
                    self.icon[item]=icon
                if item in layer.new_items :
                    layer.new_items.remove(item)

            if evt.state==0:
                #remove
                layers=(evt.data,)+tuple(evt.data.children)
                for l in layers:
                    #if item in l.links :
                    #    [self.remove(link,**kwargs) for link in tuple(l.links[item])]
                    #l.remove(item)
                    if l==self.graph :
                        icon = self.icon.pop(item,None)
                        if icon :
                            del self.items[icon.id]
                            icon.kill()
                            break
                    else :
                        icon = self.icon.get(item,None)
                        if icon :
                            icon.delete_set(l)
            if evt.kwargs.get('assess',False) :
                self.assess_itemstate(item)
            if evt.kwargs.get('update',False) :
                self.update()
        #return
        #in principle what is below is unnecessary since children are passed
        #by the user.event !
        for c in evt.states.node[evt.state]['children_states']:
            if c.state == evt.states.node[evt.state]['children_states'][c]:
                #react to it only if the child event has really been executed!
                self.react(c)

    def icon_update(self,target):
        icon=self.icon[target]
        icon.create(self.group,'all')
        icon.update()
        self.assess_itemstate(target)

    def get_info(self,item,info=None,**kwargs):
        if isinstance(item,CanvasIcon):
            item=item.item
        return self.active_graph.get_info(item,info,**kwargs)



    def get_infotypes(self,typ):
        return self.active_graph.get_infotypes(typ)

    def current_groups(self): #in case I try to use multiple groups
        return (self.group,)
        #Obsolete but in case I would like to save it :
        glist=[self.group_always]
        if self.handler :
            wid,hei=ergonomy['canvas_block_size']
            x,y=self.handler.viewpos()
            swid,shei=self.handler.viewport.size
            starti=x//wid
            startj=y//hei
            maxi = swid//wid +2 +starti
            maxj = shei//hei +2 + startj
            for i in range(starti,maxi):
                for j in range(startj,maxj):
                    try :
                        glist.append(self.group[(i,j)])
                    except :
                        pass
        return glist

    def update(self,*args):
        if user.evt.moving:
            return False
        self.surface.fill(COLORKEY)
        self.static_surface.fill((0,0,0,0) )
        if self.handler :
            for g in self.current_groups():
                for s in g :
                    #if s.rect.colliderect(self.handler.viewport.rect.move(self.handler.viewport.offset)):
                        self.surface.blit(s.image,s.rect)
                        self.static_surface.blit(s.image,s.rect)
        else :
            for g in self.current_groups():
                g.draw(self.surface)
        self.mask=pg.mask.from_surface(self.surface)


    def add_subgraph(self,subgraph=None,**kwargs):
        if subgraph in self.layers:
            return False
        if not subgraph :
            subgraph=kwargs.get('subgraph',None)
            if subgraph is None:
                print 'Adding no subgraph',debug.caller_name()
                subgraph=self.graph.Subgraph(self.graph,**kwargs)
        self.layers.append(subgraph)
        self.catch_new()
        self.set_layer(subgraph,kwargs.get('pos',0))
        self.handler.make_dependencies(True)
        return subgraph
#        self.set_active_graph(subgraph)

    def rem_subgraph(self,subgraph):
        if subgraph in self.layers:
            self.layers.remove(subgraph)
            self.set_layer(self.graph)

    def set_layer(self,graph=None,pos=0,**kwargs):
        if hasattr(graph,'__iter__'):
            for g in graph[::-1]:
                try :
                    self.layers.remove(g)
                except :
                    pass
                self.layers.insert(pos,g)
        else :
            if not graph :
                if len(self.layers)==1 :
                    return False
                graph = self.layers[-1]
            try :
                self.layers.remove(graph)
            except :
                pass
            self.layers.insert(pos,graph)
        for l in self.layers[1:]:
            self.state[l]=self.dft_graph_states.get(l,self.dft_graph_states['idle'])
        graph = self.layers[0]
        self.set_active_graph(graph)
        #print debug.caller_name()
        #print self.layers, self.state
        if self.handler and kwargs.get('signal',True):
            self.handler.signal('set_layer',graph)
        self.assess_itemstate()
        return True


    def set_active_graph(self,graph):
        prev= self.active_graph
        if graph == prev :
            return False
        self.active_graph=graph
        self.state[graph]='active'
        self.state[prev]=self.dft_graph_states.get(prev,self.dft_graph_states['idle'])
        return True

    def catch_new(self):
        """If new items have been added to some layer, add them."""
        for l in self.layers :
            for item in tuple(l.new_items):
                #print item, l
                if l == self.graph :
                    self.add(item)
                else :
                    self.add(item,layer=l)
            l.new_items=[]
        return True

    def assess_itemstate(self,items=None):
        self.catch_new()
        if items and not hasattr(items,'__iter__'):
            items = [items]
        states={}
        for sub in self.layers :
            if items:
                sitm=[i for i in items if sub.contains(i)]
            else :
                links=sub.links
                sitm=links.keys()+[i for v in links.values() for i in v]

            for i in sitm :
                states.setdefault(i,sub)

        for n,sub in states.iteritems() :

            state=self.state[sub]
            if state == 'hidden':
                self.set_view(n,'hide')
            else :
                try:
                    if not sub in self.icon[n].image_sets:
                        self.icon[n].create(self.group,sub)
                    self.icon[n].select_set(sub)
                    self.dirty=1
                except:
                    print 'CanvasError:cannot select set', n,n in self.icon, self.graph.contains(n), sub
                self.set_view(n,'show')
                if state =='ghost':
                    self.set_ghost(n,'hide')
                else :
                    self.set_ghost(n,'show')
                    if state!='active':
                        self.icon[n].set_state(state)
        return True

class CanvasHandler(UI_Widget):
    name='canvashandler'
    _canvas = None
    _surface = None
    select_opt=deepcopy(UI_Widget.select_opt)
    select_opt['auto_unselect']=True  #unselect selected by clicking anywhere else
    paint_all=True #For now, keep true

    def __init__(self,canvas,parent,size=None):
        self.view= self #TODO: reorganize canvas into handler (data gestion, layers) and handler.view= widget (icons and UI events)
        self.offset=(0,0)
        self.parent = parent
        if not size :
            size=parent.screen.get_rect().size
        self.viewport=pgrect.Rect((0,0),size)
        if canvas :
            self.canvas = canvas
        else :
            self.surface=pg.surface.Surface(parent.rect.size)
        #self.surface.set_colorkey(COLORKEY)
        self.bg=None
        self.hovering=None
        self.selected=None
        self.multiseld=[]

        self.depend=DependencyGraph()
        self.make_dependencies()

    def update(self):
        if self.canvas.animated :
            self.canvas.animated.update()
        if self.canvas.dirty:
            self.canvas.dirty=False
            self.canvas.update()

    @property
    def canvas(self):
        return self._canvas

    @property
    def data(self):
        return self.canvas.graph

    @canvas.setter
    def canvas(self,canvas):
        self._canvas = canvas
        self.surface=pg.surface.Surface(canvas.rect.size,Canvasflag)

    @property
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self,surface):
        self._surface = surface
        self.rect=self.surface.get_rect()



    def make_dependencies(self,transmit_upward=False):
        self.depend.clear()
        for l in self.canvas.layers:
            self.depend.add_dep(self.canvas,l)
        if transmit_upward:
            try:
                self.parent.make_dependencies()
            except:
                pass

    @property
    def pos(self):
        return self.canvas.pos

    def paint(self,surface=None):
        if not surface:
            surface=self.surface
            if not self.bg:
                self.surface.fill(COLORKEY)

        #self.surface.set_clip(self.viewport.get_abs_rect())

        offset=self.offset
        viewrect=self.viewport.move(offset)
        offset=(-offset[0],-offset[1])
        if self.bg :
            surface.blit(self.bg,offset)
        if self.paint_all:
            for g in self.canvas.current_groups():
                for s in g :
                    if s.rect.colliderect(viewrect):
                        surface.blit(s.image,s.rect.move(offset))
     #           g.draw(self.surface)
        else:
            #TODO: Make this work properly
            surface.blit(self.canvas.static_surface,(0,0),viewrect)
            self.paint_animated(surface,viewrect,offset)

    def paint_animated(self,surface,viewrect,offset):
        for g in self.canvas.animated:
            if g.rect.colliderect(viewrect):
                surface.blit(g.image,g.rect.move(offset))

    def select(self,*args,**kwargs):
        multi=tuple(self.multiseld)
        if UI_Widget.select(self,*args) :
            if self.selected :
                #self.signal('select',self.selected,inverse='unselect',**kwargs)
                evt=SelectEvt(self.selected.item,affects=[self,self.canvas,self.canvas.graph],source=self.name)
                user.evt.do(evt,ephemeral=True)
            elif self.multiseld!=multi :
                sel=[i.item for i in self.multiseld if not i in multi]
                unsel=[i.item for i in multi if not i in self.multiseld]
                if sel:
                    self.signal('select',*sel,inverse='unselect',**kwargs)
                if unsel:
                    self.signal('unselect',*unsel,inverse='select',**kwargs)
            else :
                self.signal('unselect',*args,inverse='select',**kwargs)
            return True
        return False

    def unselect(self,*args,**kwargs):
        if UI_Widget.unselect(self,*args) :
            self.signal('unselect',*args,inverse='select',**kwargs)
            return True
        return False

    def hover(self,hover) :
        if UI_Widget.hover(self,hover):
            #print hover, self.label(hover)
            self.signal('hover',hover,label=self.label(hover),affects=(self,hover.item))
            if self.label(hover):
                if hover.item.type=='node':
                    mopos=array(self.abspos(hover)) + (hover.rect.w*3/4,0)
                else:
                    mopos=None
                user.set_mouseover(self.label(hover),pos=mopos)
                info=self.canvas.active_graph.get_info(hover.item)
                if not info:
                    info= self.label(hover)
                else:
                    if hover.item.type=='link':
                        info=info.get('pattern','')
                    elif info.get('desc',None):
                        info=info['name']+' - '+info['desc']
                    elif 'name' in info:
                        info=info['name']
                if info:
                    self.signal('hover',hover,label=info,affects=(self,hover.item))
            else:
                self.signal('hover',hover,affects=(self,hover.item))
            return True
        return False

    def unhover(self,**kwargs):
        if UI_Widget.unhover(self,**kwargs):
            self.signal('unhover',affects=(self))
            user.kill_mouseover()
            return True
        return False

    def mousepos(self,child=None):
        return tuple(array(UI_Widget.mousepos(self,child)))#+array(self.offset))

    def abspos(self,icon=None):
        return tuple(array(self.canvas.abspos(icon))-array(self.offset))

    def drop(self):
        user.state ='idle'
        grabbed= user.grabbed
        if user.ungrab() and grabbed.item.type=='node':
            grabbed=grabbed.item
            evt=MoveEvt(grabbed, self.canvas.graph,self.canvas.pos[grabbed])
            if user.evt.do(evt,self.canvas.graph):
                self.canvas.dirty=True

    def test_hovering(self,event,**kwargs):
        canvas=self.canvas
        if 'pos' in kwargs:
            pos=kwargs['pos']
        else:
            refpos=(0,0)
            for i,j in kwargs.iteritems():
                    if i=='refpos':
                        refpos=j
            if refpos!=(0,0) and hasattr(event,'pos') :
                pos=event.pos
                pos = tuple(array(pos)-array(refpos))
            else :
                pos=self.mousepos()
        user.setpos(pos)
        hover = None
        if canvas.mask.get_at(pos) :
            if not hover:
                tmp=pgsprite.spritecollide(user.arrow,
                    [t for t in canvas.tools if t in canvas.group] ,
                    False,pgsprite.collide_circle)
                if tmp:
                    self.hover(tmp[-1])
                    return tmp[-1].event(event,**kwargs)
            try :
                hover=pgsprite.spritecollide(user.arrow,
                    [n for n in canvas.nodes if n in canvas.group] ,
                    False,pgsprite.collide_circle)[-1]
            except :
                try :
                    prelim=pgsprite.spritecollide(user.arrow,
                        [l for l in canvas.links if l in canvas.group],False)
                    while hover == None :
                        test = prelim.pop()
                        if pgsprite.collide_mask(user.arrow,test):
                            hover = test
                    #hover=pgsprite.spritecollide(user.arrow,canvas.links,False,pgsprite.collide_mask)[-1]'''
                    #hover=prelim[-1]
                except:
                    pass

            if hover and not hover.is_ghost :
                self.hover(hover)
            else :
                self.unhover()
        return hover


    def event(self,event,**kwargs):
        if event.type==30 and self.canvas.motion:
            m=self.canvas.motion[0]
            dist=array(m)-self.offset
            step=int( ergonomy['canvas_glide_speed']*1./ergonomy['animation_fps'])
            hyp=hypot(*dist)

            if hyp < step*1.5:
                self.set_offset(m,False)
                self.canvas.motion.pop(0)
            else :
                rel=hyp/ergonomy['canvas_typical_dist']
                if rel>1:
                    step=rint(step* (rel) )
                rad,angle=hypot(*dist),atan2(dist[1],dist[0])
                oldoff=self.offset
                self.set_offset( (int(step*cos(angle)),int(step*sin(angle)) ))
                if oldoff==self.offset: #blocked by boundaries)
                    self.canvas.motion.pop(0)
        handled=False
        refpos=(0,0)
        for i,j in kwargs.iteritems():
                if i=='refpos':
                    refpos=j
        if refpos!=(0,0) and hasattr(event,'pos') :
            pos=event.pos
            pos = tuple(array(pos)-array(refpos))
        else :
            pos=self.mousepos()

        if event.type==pg.KEYDOWN:
            if self.keymap(event,pos=pos):
                return True

        canvas=self.canvas
        if not canvas.rect.collidepoint(pos):
            self.drop()
            return False
        if not canvas.mask.get_at(pos) and user.state == 'idle' and not event.type in (pg.MOUSEBUTTONDOWN,pg.MOUSEBUTTONUP ):
            if not event.type==pg.MOUSEMOTION or not pg.mouse.get_pressed()[0]:
                self.unhover()
                return handled
            else :
                self.canvas.motion=[]
                return self.set_offset(-array(event.rel))

        if user.state=='grab' and event.type == pg.MOUSEMOTION :
            if pg.mouse.get_pressed()[0] :
            #Drag-and-drop
                try :
                    foc=user.grabbed
                    rate=ergonomy['nodes_stickyness_to_mouse']
                    rel=(event.rel[0]+(pos[0]-foc.rect.center[0])*rate,event.rel[1]+(pos[1]-foc.rect.center[1])*rate)
                    rect =foc.drag(rel)
                    return True
                except:
                    print 'graberror'

            else :
                self.drop()
                return True

        if user.state == 'idle'  and event.type in (pg.MOUSEBUTTONDOWN,pg.MOUSEBUTTONUP,pg.MOUSEMOTION) :
            hover=self.test_hovering(event,pos=pos)

            if event.type == pg.MOUSEBUTTONDOWN :
                    if not hover and self.select_opt['auto_unselect'] :
                        self.unselect()
                    #print [nicon.id for nicon in  pgsprite.spritecollide(user.arrow,canvas.group,False,pgsprite.collide_circle)]
                    #print [nicon.id for nicon in  canvas.group.get_sprites_at(pos)]
                    if event.button ==1 :
                        handled=self.left_click(hover,event)
                    elif event.button==3 :
                        handled = self.right_click(hover,event)
                        '''try :
                            print self.hovering.id, self.hovering.node.val, self.hovering.states
                        except :
                            print 'Not a node'''
                    elif event.button>3:
                        handled=self.fast_edit(hover,event)
            elif hover and  event.type == pg.MOUSEMOTION and  pg.mouse.get_pressed()[0]:
                self.drag()
        if not handled :
            if event.type == pg.MOUSEBUTTONUP :
                self.drop()
                handled = True
        if handled :
            self.canvas.dirty=True

        '''
        if False and user.state=='idle':
            pgevent.set_blocked(pg.MOUSEMOTION)
        else :
            pgevent.set_allowed(pg.MOUSEMOTION)'''
        return handled

    def drag(self):
        if  self.hovering and self.hovering.draggable:
            user.state='grab'
            user.grab(self.hovering)
            return True
        return False

    def left_click(self,target,event=None):
        if not target :
            return False
        typ=target.item.type
        if target == user.just_clicked :
            user.just_clicked=None
            return self.double_click(target)
        else :
            pg.time.set_timer(31,ergonomy['double_click_interval'])#just clicked remover
            user.just_clicked=target

        pg.time.delay(40)
        evts= pgevent.get((pg.MOUSEMOTION,pg.MOUSEBUTTONUP,pg.MOUSEBUTTONDOWN))
        if not evts or evts[0].type==pg.MOUSEBUTTONUP:
            self.select(self.hovering)
            user.state='idle'
            return True
        else :
            newevent=evts[0]
        if newevent.type == pg.MOUSEMOTION and typ=='node':
            return self.drag()
        elif newevent.type == pg.MOUSEBUTTONDOWN :
            # Impossible for a human in such a short delay, but catch it anyway
            return self.double_click(target)

        return self.event(newevent)

    def double_click(self,target, event=None):
        try:
            target=target.item
        except:
            pass
        if self.canvas.active_graph.contains(target):
            self.signal('edit',target)
        return True

    def right_click(self,target,event=None):
        return False

    def fast_edit(self,target,event):
        #using the mousewheel fo fast edit
        if event.button==4:
            d=1
        elif event.button==5:
            d=-1
        if pg.key.get_pressed()[pg.K_v]:
                item=target.item
                if item.type in ('node','link'):
                    self.canvas.change_infos(item,val=d*.1,additive=True)
                    return True
        return False

    def menu(self,*args):
        return False

    def signal(self,signal,*args,**kwargs):
        kwargs.setdefault('affects',(self,self.canvas))
        event=Event(*args,type=signal,source=self.name,**kwargs)
        self.canvas.dirty=True
        if user.ui:
            user.evt.pass_event(event,self,True)
        else:
            pass #for signals given before ui is complete
#        self.parent.receive_signal(signal)


    def keymap(self,event,**kwargs):
        pos = kwargs.get('pos',None)
        if event.key == pg.K_TAB :
            if len(self.canvas.layers) > 1 :
                self.canvas.set_layer()
                return True

        if event.key in (pg.K_DOWN,pg.K_UP,pg.K_LEFT,pg.K_RIGHT):
            delta=ergonomy['key_graph_move_rate']
            offset=array(0)
            if event.key==pg.K_DOWN :
                offset = array((0,delta))
            if event.key==pg.K_UP :
                offset = array((0,-delta))
            if event.key==pg.K_RIGHT :
                offset =  array((delta,0))
            if event.key==pg.K_LEFT :
                offset =  array((-delta,0))
            if offset.any():
                self.canvas.motion=[]
                return self.set_offset(offset)
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_n and self.canvas.active_graph==self.canvas.graph:
                self.add_node(None,None,pos=self.mousepos())

        return False

    def set_offset(self,offset,additive=True):
        if additive:
            offset=array(offset)
            ioff =array(self.offset)
            offset=tuple(ioff+offset)
        rect=pgrect.Rect(offset,self.viewport.size).clamp(self.canvas.rect)
        if rect.topleft != self.offset :
            self.offset=rect.topleft

#            self.event(pgevent.Event(pg.MOUSEMOTION,pos=(0,0),rel=tuple(offset)))
            return True
        return False

    def center_on(self,item_or_pos,glide=True):
        if hasattr(item_or_pos,'__iter__'):
            pos = array( item_or_pos)
        else :
            item = item_or_pos
            if hasattr(item,'item'):
                icon = item
            else :
                icon = self.canvas.icon[item]
            if item.type == 'node':
                pos=array(self.canvas.pos[item])+array(icon.rect.size)/2
            elif item.type == 'link':
                ip=item.parents
                pos = array(self.canvas.pos[ip[0]])+array(self.canvas.pos[ip[1]])
                pos /=2
            else :
                return False
        pos -=array(self.viewport.size)/2
        if not glide or (glide==True and ergonomy['canvas_glide_speed']<0 ):
            self.set_offset([int(i) for i in pos],False)
        else:
            pos= tuple(int(i) for i in pos)
            if not self.canvas.motion or  pos != self.canvas.motion[-1]:
                self.canvas.motion.append(  pos)

    def label(self,item):
        try:
            return item.label
        except:
            pass
        if hasattr(item,"item"): #if we receive an icon
            item=item.item
        infos = self.canvas.get_info(item)
        if item.type=='node':
            return '(N'+str(item.ID)+') ' + infos['name'] + ': '+ infos['desc']
        elif item.type=='link':
            return '(L'+str(item.ID)+') ' + infos['name'] + ': '+ infos['desc']



class CanvasEditor(CanvasHandler):

    def __init__(self,*args):
        CanvasHandler.__init__(self,*args)


    def bgmenu(self,main=True):
        if main :
            bgmenu = [
            ('Add node',lambda p=self.mousepos():self.add_node(None,None,pos=p)),
                ('Add subgraph',self.add_subgraph),
                ('Manage subgraphs',self.manage_subgraphs),
                ]
            if not ergonomy['canvas_external_control']:
                bgmenu+=[
                            ('Save graph',self.save_graph_menu),
                ('Load graph',self.load_graph_menu)]
        else :
            bgmenu = [
                ('Manage subgraphs',self.manage_subgraphs),
                ]
        if not user.ui.view['nodelist']:
            bgmenu += [('Node list',lambda:user.ui.show('nodelist') )]
        return bgmenu

    def menu(self,event=None,**kwargs):
        target= kwargs.get('target',self.hovering)
        if not target :
            typ='bg'
        else :
            typ=target.item.type
        if self.canvas.active_graph==self.canvas.graph :
            return self.maingraph_menu(target,typ,event=None)
        else :
            return self.subgraph_menu(target,typ,event=None)
        return ()

    def maingraph_menu(self,target,typ,event=None):
        struct=()
        if not ergonomy['edit_on_select']:
            struct+=( ('Edit',lambda t=target: self.signal('edit',t)), )

        if typ == 'node':
            struct +=( ('Add link',lambda t=target: self.start_linkgrabber(t)),
            ('Delete node',lambda t=target: self.rem_node(t.node))
            )
            return struct
        if typ == 'link' :
            struct += (('Delete link',lambda t=target: self.rem_node(t.link)),
            )
            return struct
        if typ == 'bg' :
            return self.bgmenu()
        return struct

    def subgraph_menu(self,target,typ,event=None):
        act=self.canvas.active_graph
        struct=()

        if typ in ('node','link'):
            if self.canvas.active_graph.contains(target.item) :
                if not ergonomy['edit_on_select']:
                    struct+=( ('Edit',lambda t=target: self.signal('edit',t)), )
                struct +=( ('Remove',
                    lambda: self.rem_node(target.item,layer=act,assess=True)),)
            else :
                struct +=( ('Import',
                    lambda: self.add_node(target.item,layer=act,addrequired=True,assess=True)),)
            return struct
        if typ == 'bg' :
            return self.bgmenu(False)
        return struct


    def add_node(self,item=None,layer=None,**kwargs):
        act=self.canvas.active_graph
        if not item:
            item=act.Node()
            kwargs.setdefault('pos',self.mousepos())
        if not layer:
            layer= self.canvas.graph
        evt=AddEvt(item,layer,**kwargs)
        user.evt.do(evt )
        #self.canvas.add(act.Node(),pos=self.mousepos() )
        return

    def rem_node(self,item,layer=None,**kwargs):
        if not layer:
            layer= self.canvas.graph
        evt=AddEvt(item,layer,inverted=True,**kwargs)
        user.evt.do(evt)
        return


    def add_subgraph(self):
        self.canvas.add_subgraph()
        return

    def manage_subgraphs(self):
        return

    def save_graph_menu(self):
        self.parent.save_menu('graph', self.save_graph,default=self.canvas.graph.name)
        return

    def save_graph(self,fil):
        fout = fopen('editor.log','w')
        self.canvas.graph.name=fil
        fil = database['graph_path']+fil+database['graph_ext']
        fout.write('current_graph:'+fil)
        fout.close()
        self.canvas.save_graph_to_file(fil)

    def start_linkgrabber(self,source,**infos):
        grabber=LinkGrabber(self.canvas)
        grabber.rect.center = self.mousepos()
        user.grab(grabber)
        link=self.canvas.active_graph.Link((source.node,grabber))
        link.required=(source.node,)
        self.canvas.add(link,state='ghost',**infos)

    def end_linkgrabber(self,grabber,event):
        user.ungrab()
        newevent=pgevent.Event( pg.MOUSEMOTION,pos=self.mousepos(),rel=(0,0))
        self.event(newevent)
        if isinstance(self.hovering,self.canvas.NodeIcon):
            for i in grabber.ilinks :
                newp=[self.hovering.node if p==grabber else p for p in i.link.parents]
                if newp[0]!=newp[1]:
                    infos= self.canvas.get_info(i.link)

                    #self.canvas.rewire(i.link,tuple(newp))
                    #i.rm_state('ghost')
                    self.canvas.remove(i.link)
                    evt = AddEvt(self.canvas.active_graph.Link(tuple(newp)),self.canvas.active_graph,infos=infos )
                    user.evt.do(evt,self)
                else :
                    self.canvas.remove(i.link)
#                i.create(self.canvas.group)
        else :
            for i in grabber.ilinks:
                self.canvas.remove(i.link)
        grabber.kill()

        return True

    def load_graph_menu(self):
        self.parent.load_menu('graph',self.canvas.set_graph_from_file,new=self.canvas.new_graph)
        return

    def call_menu(self,menu=None,**kwargs):
        if not menu:
            menu=self.menu(**kwargs)
        if menu:
            if 'target' in kwargs:
                tgt=kwargs['target']
                pos=self.abspos(tgt)+array(tgt.rect.size)/2
                kwargs['pos']=pos
            user.ui.float_menu(menu,oneshot=True,**kwargs)

    def right_click(self,target,event=None):
        if not target:
            return False
        self.call_menu(target=target)
        return True
