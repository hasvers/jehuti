# -*- coding: utf-8 -*-
from gv_windows import *
from gv_canvas import *
from gv_basecanvas import *


class StatusBar(Window):
    fixsize=True
    clickthrough=True
    def __init__(self,interface,**kwargs):
        size =(interface.available.w,graphic_chart['statusbar_width'])
        Window.__init__(self,interface,size,margin=graphic_chart['statusbar_margin'],alpha=graphic_chart['window_hover_alpha'],**kwargs)
        self.make(kwargs.get('menu',None))

    def make(self,menu=None):
        self.clear()
        if menu:
            for i,j in menu:
                txt=self.add('dropmenu',val=(i,j),selectable=True,pos=(0,0),bgcolor=graphic_chart['menu_button_bgcolor'])
                txt.fixsize=True
            #self.add('text',val='|',pos=(0,1), width=20,fixsize=True)
        self.status=TextField(self)#,w=self.active_rect.w,h=self.active_rect.h,fixsize=True)
        self.add(self.status,pos=(0,1))
    def update(self):
        if user.status != self.status.val :
            self.status.set_val(user.status)
            #self.status.redraw()
        Window.update(self)

    def set_state(self,state,*arg,**kwargs):
        if super(StatusBar,self).set_state(state,*arg,**kwargs):
            if 0 and self.state == 'hover':
                self.image.set_alpha(graphic_chart['statusbar_hover_alpha'])
            return True
        return False

    def react(self,evt):
        if evt.type=='status':
            self.update()

class NodeList(Window):
    name='nodelist'
    def __init__(self,interface,handler=None,**kwargs):
        mrg=graphic_chart['nodelist_margin']
        size =(graphic_chart['nodelist_width'],interface.available.h)
        Window.__init__(self,interface,size,maxsize=size,margin=mrg,
            alpha=graphic_chart['window_hover_alpha'],**kwargs)
        if handler is None:
                    self.handler=interface.canvas.handler
        else:
            self.handler=handler

        self.make()

    def node_select(self,n):
        self.handler.center_on(n)
        self.handler.select(self.handler.canvas.icon[n])

    def clear(self):
        Window.clear(self)
        self.interface.depend.rem_dep(self)

    def make_dependencies(self):
        self.interface.depend.add_dep(self,self.handler)
        self.interface.depend.add_dep(self,self.handler.canvas.graph)

    def make(self):
        self.clear()
        handler=self.handler
        self.list= sorted(tuple ( [( handler.label(n),n) for n in handler.canvas.active_graph.nodes]),
            key=lambda e: e[1].ID )
        self.hide=self.add('text',val='Close',selectable=True,
            output_method=lambda:self.interface.hide(self.name ))
        self.field=FieldList(self,self.list,w=self.width,
            output_method=self.node_select ,scrollable='v')#,output_method=interface.canvas.set_view)
        self.add(self.field)
        self.make_dependencies()

    def renew(self):
        nlist= sorted(tuple ( [(self.handler.label(n),n) for n in self.handler.canvas.active_graph.nodes]),
            key=lambda e: e[1].ID)
        if nlist != self.list :
            self.list=nlist
            self.field.set_list(nlist)

    def react(self,evt):
        if not self.parent.view[self.name]:
            return
        if 'select' in evt.type:
            self.field.unselect()
        if 'add' in evt.type or 'change' in evt.type:
            self.renew()
        if 'set_graph' in evt.type:
            self.make()

    def refresh(self):
        #whenever the window is unhidden
        self.renew()



class EditorMenu(DragWindow):
    #For anything whose editing may justify undo/redo
    title = 'EditorMenu'
    name='editormenu'
    attrs=()
    ref=None
    infosource = None
    itemwrite=False
    #write attributes on item directly (instead of infos in a datastructure)
    #used for simple items that cannot belong to multiple datastructures (e.g. scripts, quotes)
    ephemeral=False #for editormenus that should not produce undoable changes
    scrollable='v'

    def __init__(self,interface,infosource=None,**kwargs):
        size =graphic_chart['float_base_size']
        self.confirm=kwargs.pop('askconfirm',False)
        kwargs.setdefault('maxsize',array(interface.screen.get_rect().size)*.75)
        DragWindow.__init__(self,kwargs.pop('dragarea',interface.screen),interface,size,**kwargs)
        for i,j in kwargs.iteritems() :
            if i == 'ref':
                self.ref=j
            if i=='attr':
                self.attrs=j
            if i=='itemwrite':
                self.itemwrite=j
            if i=='ephemeral':
                self.ephemeral=j
        self.clear()
        self.initparams=kwargs
        self.last_changed=None
        if not self.infosource:
            self.infosource=infosource

        self.make()
        if 'ref' in kwargs :
            self.set_ref(kwargs['ref'])


    @property
    def data(self):
        if hasattr(self.infosource,'data'):
            return self.infosource.data
        else :
            return self.infosource

    @staticmethod
    def list_format(flist):
        if len(flist[0])<5:
            #conversion between format for parse and format for set_ref (maybe rationalize this someday)
            nflist=[]
            for i in flist:
                if len(i)>2:
                    opts=i[2]
                else:
                    opts={}
                ni=(opts.pop('title',i[0].capitalize()),opts.pop('width',graphic_chart['window_field_std_size'][0]) )
                nflist.append(i[:2]+ni+(opts,))
            flist=tuple(nflist)
        return flist

    def clear(self):
        DragWindow.clear(self)
        self.drag={}
        self.input={}
        self.listsel={}
        self.extsel={}
        self.immutable={}
        self.menu={}
        self.lists={}
        self.chgevt={}

    def make_attrs(self,*args):
        return 1

    def make(self,**kwargs):
        self.clear()
        v=0
        self.add('text',val=self.title,pos=(v,0),width=100,height=30,colspan=2)
        if not self.confirm:
            self.add('text',val='Close',pos=(v,2),width=50,selectable=True,output_method=lambda e=self.name:self.interface.hide(e))
        else:
            self.add('blank',height=30,width=10,pos=(v,2))
        self.cats={'input':self.input,'array':self.input, 'drag':self.drag,'arrowsel':self.listsel,
            'listsel':self.listsel, 'toggle':self.listsel,'list':self.lists,'inputlist':self.lists,'menu':self.menu,
            'extsel':self.extsel,'text':self.immutable}
        if 'cats' in kwargs :
            for i,j in kwargs['cats'].iteritems():
                self.cats[i]=j
        for a in self.attrs :
            if a[4].get('extfield',False):
                #used for fields contained elsewhere (e.g. in a toggler)
                continue
            v+=1
            self.add('blank',height=30,width=10)
            self.add('text',val=a[2],pos=(v,1),width=80)
            if not a[1] in ('list','inputlist'):
                typ,opts=a[1],{}
                opts.update(a[4])
                if typ=='menu':
                    typ='text'
                    opts['selectable']=1
                if 'val' in a[4]:
                    self.cats[a[1]][a[0]]=self.add(typ,pos=(v,2),width=a[3],**opts)
                else :
                    if self.ref:
                        if self.itemwrite or a[4].get('itemwrite',False):
                            val = getattr(self.ref,a[0])
                        else:
                            val = self.data.get_info(self.ref,a[0])
                        if val is None and a[1]=='arrowsel':
                            val=a[4].get('values')[0]
                    else:
                        val=0
                    self.cats[a[1]][a[0]]=self.add(typ,val=val,
                        pos=(v,2),width=a[3],**opts)
                if a[1]=='toggle':
                    tog=self.cats[a[1]][a[0]]
                    if not hasattr(self,'trueattrs'):
                        self.trueattrs=self.attrs
                    for x in EditorMenu.list_format(tog.template):
                        if not x in self.attrs:
                            self.attrs+= x,
                        x[4].setdefault('extfield',True)
                        self.cats[x[1]][x[0]]=tog.container.fieldict[x[0]]

            else :
                kw={}
                kw.update(a[4])
                kw['menu']={}
                kw['menu'].update(a[4].get('menu',{'type':'input'}))
                kw['menu'].setdefault('caller',self)
                self.cats[a[1]][a[0]]=self.add(a[1],val=[('None','')], pos=(v,2),width=a[3],**kw)

        if self.confirm:
            cont = FieldContainer(self,margin=8,maxsize=self.maxsize)
            self.ok_field=cont.add('text',val='Ok',output_method= self.confirmed,selectable=True,pos=(0,0),width=50)
            self.cancel_field=cont.add('text',val='Cancel',output_method=self.cancelled,selectable=True,pos=(0,1),width=50)
            self.set_command(self.ok_field,'exit')
            self.set_command(self.cancel_field,'exit')
            cont.update()
            self.add('blank',height=30,width=10,pos=(v+1,1))
            self.add(cont,pos=(v+1,2))

        self.catch_new()

    def renew_toggler_attr(self):
        self.attrs=self.trueattrs[:]
        for a in self.trueattrs :
            if a[1]=='toggle':
                tog=self.cats[a[1]][a[0]]

                for x in EditorMenu.list_format(tog.template):
                    if not x[0] in [z[0] for z in self.attrs]:
                        self.attrs+= x,
                    x[4].setdefault('extfield',True)
                    self.cats[x[1]][x[0]]=tog.container.fieldict[x[0]]
        self.set_ref(self.ref)


    def make_dependencies(self):
        self.interface.depend.add_dep(self,self.ref)
        self.interface.depend.add_dep(self,self.infosource)

    def set_ref(self,ref,renew=True):
        for i,j in self.listsel.iteritems() :
            #for listsels that need to be updated with each change of ref
            try:
                j.set_values(getattr(ref,i+'s'))
            except:
                pass

        if self.ref :
            user.ui.depend.rem_dep(self,ref)
        self.ref=ref
        self.make_dependencies()
        if renew:
            self.renew_chgevts()
        for a in self.attrs :
            field = self.cats[a[1]][a[0]]
#            field.unbind_command()
            self.rem_command(field)
            if 'values' in a[4] and hasattr(field,'values') and a[4]['values']!=field.values:
                #TODO: this is not very clean, in principle other options could change as well
                field.set_values(a[4]['values'])
            if a[1]=='inputlist' and not a[4].get('freeform',False) :
                if self.itemwrite or a[4].get('itemwrite',False):
                    inf = getattr(ref,a[0])
                else:
                    inf=self.data.get_info(ref,a[0])
                meth='confirm'
                val=[]
                opts=a[4].get('menu',{'type':'input'})
                typ=opts['type']
                field.opts={}
                field.opts.update(opts)
                field.opts.setdefault('caller',self)
                if hasattr(inf,'keys'):
                    field.sendall=False
                    field.output_method=lambda i,t=a[0] :self.set_info(t,dict(i))
                    for i,j in inf.iteritems() :
                        val.append ((str(i)+ ': '+str(j),(i,j) ))
                else :
                    field.sendall=True
                    field.output_method=lambda i,t=a[0] :self.set_info(t,i)
                    for i in inf :
                        val.append ((str(i),i))
                if not val:
                    val=[('None','')]
                field.selectable=True
                field.set_list(val)

            elif a[1]=='menu':
                if self.itemwrite or a[4].get('itemwrite',False) :
                    val = getattr(self.ref,a[0])
                else:
                    val = self.data.get_info(self.ref,a[0])
                if val is None and a[1]=='arrowsel':
                    val=a[4].get('values')[0]
                if field.val!=val:
                    field.set_val(val)
                ext=False # lambda s=self.cats[a[1]][a[0]]: s.unselect()
                geth=lambda e,t=a[0] :self.set_info(t,e)
                opts={}
                opts.update(a[4])
                opts.setdefault('val',val)
                if ext:
                    opts['on_exit']=ext
                typ=opts.pop('type','input')
                opts.setdefault('caller',self)
                meth = lambda t=typ, m=geth,o=opts: self.parent.input_menu(t,m,**o)
            else :
                if 0 and a[4].get('extfield',0) and a[4].get('val',0) and not (a[4].get('values')
                         and not val in a[4]['values']):
                    #only case when field value has precedence over current item attribute
                    #is extfield from a toggler, to conserve memory of non-validated changes
                    val=a[4]['val']
                    #TODO:Doesn't work!!!
                else:
                    if self.itemwrite or a[4].get('itemwrite',False):
                        val = getattr(self.ref,a[0])
                    else:
                        val = self.data.get_info(self.ref,a[0])
                if val is None or a[4].get('values') and not val in a[4]['values']:
                    oldval,val=val,a[4].get('val',a[4].get('values',[None])[0])
                    #TODO: MAYBE DANGEROUS, I automatically replace values that are None
                    if oldval is None:
                        if not self.confirm:
                            if self.itemwrite or a[4].get('itemwrite',False):
                                if hasattr(self.ref,'set_attr'):
                                    self.ref.set_attr(a[0],val)
                                else:
                                    setattr(self.ref,a[0],val)
                            else:
                                self.data.set_info(self.ref,a[0],val)
                        else:
                            self.chgevt[a[0]].kwargs[a[0]]=val
                field.set_val(val)
            #self.cats[a[1]][a[0]].unbind_command()
            #if  not a[1] in ('list','menu'):
                #meth =lambda e,t=a[0] :self.infosource.change_infos(self.ref,**{t:e})
                meth =lambda e,t=a[0]: self.set_info(t,e)
            self.set_command(field, (meth, ()) )
            #field.bind_command(meth)
            if a[1]=='toggle':
                self.set_command(field, (self.renew_toggler_attr, ()) )
                self.set_command(field,'do')
        self.compute_pos()
        self.rect.clamp_ip(self.interface.rect)
        self.interface.pos[self]=array(self.interface.abspos())+array(self.rect.topleft)

    def change_method(self,a,meth):
        field=self.cats[a[1]][a[0]]
        self.rem_command(field)
        self.set_command(field, (meth, ()) )
        #self.cats[a[1]][a[0]].unbind_command()
        #self.cats[a[1]][a[0]].bind_command(meth)

    def set_info(self,attr,info):
        evt=self.chgevt[attr]
        if hasattr(info,'keys'):
            evt.kwargs.setdefault(attr,{}).update(info)
        else:
            evt.kwargs[attr]=info
        if not self.confirm:
            self.send_info(attr)
        else:
            #If this editor menu asks for confirmation before making changes,
            #run the event in secret, changing the infos without warning handlers
            #and then undo it by cancel
            evt.prepare((evt.state,1) )
            if evt.run(1):
                evt.state=1
            else:
                raise Exception('EditMenuError: {} couldnt do {}'.format(self, evt) )

        for a in self.attrs:
            if a[0]==attr and a[4].get('remake',False):
                self.make_attrs()
                self.set_ref(self.ref, not self.confirm)

    def confirmed(self):
        for attr, evt in self.chgevt.iteritems():
            if evt.state==0:
                self.send_info(attr)
            else:
                user.evt.pass_event(evt,self,ephemeral=self.ephemeral)
        self.renew_chgevts()

    def cancelled(self):
        for attr, evt in self.chgevt.iteritems():
            if evt.state>0:
                #undo evt in secret, see comment in set_info
                evt.prepare( (evt.state,0) )
                if evt.run(0):
                    evt.state=0
                else:
                    raise Exception('EditMenuError: {} couldnt undo {}'.format(self, evt) )
                #user.evt.go(evt,self,0,ephemeral=self.ephemeral)

    def send_info(self,attr):
        #renew all events if undone state or not continuous input
        tim=pg.time.get_ticks()
        self.last_changed=(attr,tim)
        evt=self.chgevt[attr]

        user.evt.do(evt,self,1,ephemeral=self.ephemeral)
        if not self.confirm:
            if self.chgevt[attr].state ==0 or (self.last_changed
                and tim - self.last_changed[1] > ergonomy['input_stop_delay']):
                    self.renew_chgevts(attrs=(attr,) )


    def refresh_fields(self):
        #UNUSED FOR NOW
        cat={a[0]:a[1] for a in self.attrs}
        for attr, evt in self.chgevt.iteritems():
            if attr in evt.kwargs and self.cats[cat[attr] ][attr].val!=evt.kwargs[attr]:
                self.cats[cat[attr] ][attr].set_val(evt.kwargs[attr])


    def renew_chgevts(self,**kwargs):
        attrs=kwargs.get('attrs',[a[0] for a in self.attrs] )
        desc={a[0]:a[2] for a in self.attrs if a[0] in attrs}
        opt={a[0]:a[4] for a in self.attrs if a[0] in attrs}
        for a in attrs:
            if a != kwargs.get('exception',None):
                self.chgevt[a]=ChangeInfosEvt(self.ref,self.data, update=True,
                    itemwrite= self.itemwrite or opt[a].get('itemwrite',False),
                        source='editor'+str(id(self)))
                self.chgevt[a].desc='Change '+desc[a].lower()

    def kill(self,*args,**kwargs):
        if user.ui:
            user.ui.depend.rem_dep(self,self.ref)
            user.ui.depend.rem_dep(self,self.infosource)
        DragWindow.kill(self,*args,**kwargs)

    def renew(self):
        user.ui.depend.rem_dep(self,self.ref)
        user.ui.depend.rem_dep(self,self.infosource)
        self.make()

    def attr_filter(self,types,renew=True):
        if set(a[0] for a in self.attrs) != set(types) :
            attrs = list(self.__class__.attrs)
            if set(types) & set(a[0] for a in attrs) == set(a[0] for a in self.attrs):
                #all adimissible types are covered
                return False
            for a in tuple(attrs) :
                if not a[0] in types :
                    attrs.remove(a)
            self.attrs=tuple(attrs)
            if renew:
                self.renew()
            return True
        return False

    def react(self,evt):
        if not self.interface.view.get(self.name,False):
            return
        if 'change' in evt.type and evt.item==self.ref :
            if not self.queue: #prevents destruction of queued changes
                self.set_ref(self.ref,False)
        #if 'select' in evt.type:
            #for field in self.extsel:
                #if field.is_selected:
                    #field.val=evt.item
                    #field.parent.unselect(field)


class SidePanel(EditorMenu):#Template
    title = 'Sidepanel'
    name='sidepanel'
    attrs=()
    ref=None
    infosource = None
    scrollable='v'
    draggable=False
    def __init__(self,interface,infosource,**kwargs):
        size =(graphic_chart['sidepanel_width'],interface.available.h)
        EditorMenu.__init__(self,interface,infosource,minsize=size,margin=graphic_chart['sidepanel_margin'],
            alpha=graphic_chart['window_hover_alpha'],**kwargs)


    def react(self,evt):
        EditorMenu.react(self,evt)

        if 'kill_dependencies' in evt.type:
            user.ui.hide('sidepanel')
            self.renew()



class NodePanel(SidePanel):
    title = 'Node editor'
    attrs=(
        ('name','input','Name',80,{'charlimit':10}),
        ('genre','arrowsel','Genre',120,{'values':Graph.Node.genres}),
        ('val','drag', 'Magnitude',80,{'minval':.5,'maxval':2.}),
#        ('truth','drag','Truth',80,{'color':graphic_chart['icon_node_fill_colors'][:2]}),
        ('desc','input','Description',120,{'height':200,'wrap':True}))
    def __init__(self,interface,infosource,ref=None,**kwargs):

        self.ref=ref
        self.interface=interface
        self.infosource=infosource
        self.attr_filter(self.data.get_infotypes('node'),False)
        SidePanel.__init__(self,interface,infosource,**kwargs)

    @property
    def data(self):
        return self.infosource.active_graph

    def set_ref(self,ref,renew=True):
        self.attr_filter(self.data.get_infotypes('node'))
        SidePanel.set_ref(self,ref,renew)

    def react(self,evt):
        SidePanel.react(self,evt)
        if 'layer' in evt.type:
            try:
                self.set_ref(self.ref,True)
            except:
                user.ui.hide('sidepanel')
                self.renew()

class LinkPanel(SidePanel):
    title='Link editor'
    attrs=[
        ('name','input','Name',80,{'charlimit':10}),
        ('genre','arrowsel','Genre',120,{'values':Graph.Link.genres}),
        ('val','drag', 'Magnitude',80,{'minval':.5,'maxval':2.}),
        ('desc','input','Description',120,{'height':200,'wrap':True})]


    def __init__(self,interface,infosource,link=None,**kwargs):
        self.ref=link
        self.interface=interface
        self.infosource=infosource
        self.attr_filter(self.data.get_infotypes('link'),False)
        SidePanel.__init__(self,interface,infosource,**kwargs)

    @property
    def data(self):
        return self.infosource.active_graph

    def set_ref(self,ref,renew=True):
        self.attr_filter(self.infosource.get_infotypes('link'),False)
        SidePanel.set_ref(self,ref,renew)

    def react(self,evt):
        SidePanel.react(self,evt)
        if 'layer' in evt.type:
            try:
                self.set_ref(self.ref,False)
            except:
                user.ui.hide('sidepanel')
                self.renew()


class LayerMenu(DragWindow):
    #Floating menu for layers
    title = 'Layer Menu'
    name='layermenu'
    attrs=()
    ref=None
    handler = None
    scrollable='v'

    def __init__(self,interface,infosource=None,**kwargs):
        size =graphic_chart['float_base_size']
        kwargs.setdefault('maxsize',array(array(interface.screen.get_rect().size)*.75,dtype='int'))
        DragWindow.__init__(self,kwargs.pop('dragarea',interface.screen),interface,size,**kwargs)
        self.clear()
        self.handler=infosource
        self.make()

    @property
    def data(self):
        if hasattr(self.handler,'data'):
            return self.handler.data
        else :
            return self.handler

    def clear(self):
        DragWindow.clear(self)
        self.interface.depend.rem_dep(self,self.handler)
        self.interface.depend.rem_dep(self,self.data)
        self.namefield={}
        self.hidefield={}
        self.editfield={}
        self.delfield={}

    def make_dependencies(self):
        self.interface.depend.add_dep(self,self.handler)
        self.interface.depend.add_dep(self,self.data)

    def make(self,**kwargs):
        self.clear()
        self.make_dependencies()
        v=0
        self.add('text',val=self.title,pos=(v,0),width=100,height=30,colspan=2)
        self.add('text',val='Close',pos=(v,2),width=50,selectable=True,
            output_method=lambda e=self.name:self.interface.hide(e))
        for l in self.data.layers[::-1]:
            info=self.data.get_info(l)
            v+=1
            if l==self.handler.active_layer:
                color='g'
                select=False
                meth=None
            else:
                color='a' #Noeffect when selectable
                select=True
                meth= lambda lay=l:self.handler.set_active_layer(lay)
            self.namefield[l]=self.add('text',val=info['name'], pos=(v,1),color=color,
                selectable=select,output_method=meth)
            self.add('blank',width=30, pos=(v,2))
            self.hidefield[l]= self.add('text',val='',pos=(v,3),selectable=1)
            self.make_hidefield(l)
            self.editfield[l]= self.add('text',val='Edit', selectable=1,
                output_method=lambda e=l:self.handler.signal('edit',e), pos=(v,4))
            self.delfield[l]= self.add('text',val='Delete', selectable=1,
                output_method=lambda e=l:self.handler.rem_layer(e), pos=(v,5))
        v+=1
        self.add('text',val='Add',selectable=True, pos=(v,0),
            output_method=self.handler.add_layer )
        self.add('text',val='Up',selectable=True, pos=(v,2),
            output_method=self.handler.layer_up )
        self.add('text',val='Down',selectable=True, pos=(v,3),
            output_method=self.handler.layer_down )

    def make_hidefield(self,l):
        field= self.hidefield[l]
        if self.data.get_info(l,'state') in ('ghost','hidden'):
            text='Show'
            state='idle'
        else:
            text='Mask'
            state='ghost'
        field.set_val(text)
        output_method=lambda e=l,s=state:user.evt.do(ChangeInfosEvt(l,self.data,state=s) )
        self.rem_command(field)
        field.bind_command(output_method)

    def react(self,evt):
        if 'layer' in evt.type or 'add' in evt.type  and  hasattr(evt.item,
                'type') and 'layer' in evt.item.type :
            self.make()
        if 'change' in evt.type and  hasattr(evt.item,
                'type') and 'layer' in evt.item.type :
            if 'name' in evt.kwargs:
                self.namefield[evt.item].set_val(self.data.get_info(evt.item,'name'))
            if 'state' in evt.kwargs:
                self.make_hidefield(evt.item)