# -*- coding: utf-8 -*-

from gam_import import *


class SettingPanel(SidePanel):
    title = 'Setting editor'
    attrs=(
        #('name','input','Title',100,{'charlimit':20}),
        ('bg','arrowsel','Background',120,{
            'values': ['None']+[i for i in olistdir(database['backgrounds']) if not
            os.path.isdir(os.path.join(database['backgrounds'],i )) ] }),
        )


class PlaceSprite(DataItem):
    dft={'name':'Sprite',
        'set':'default',
        'source':'common/default',
        'scale':1.,
        }
    SpriteID=0
    def __init__(self,*args,**kwargs):
        DataItem.__init__(self,*args,**kwargs)
        PlaceSprite.SpriteID+=1
        self.type='sprite'
        if self.name==self.dft['name']:
            self.name+=str(PlaceSprite.SpriteID)
    def __repr__(self):
        return self.name

class PlaceSpriteIcon(BaseCanvasIcon):
    mutable=1
    def make_surface(self,size,mod,*args,**kwargs):
        item=self.item
        iset=self.canvas.handler.data.get_info(item,'set')
        if not iset:
            iset='default'
        #path=database['{}_path'.format(self.canvas.handler.data.datatype)]
        path=database['scene_path']+item.source
        try:
            img=image_load(path+'/'+iset+'.png').convert_alpha()
        except:
            img=image_load(path).convert_alpha()
        img=pg.transform.smoothscale(img, tuple(int(x*item.scale) for x in array(img.get_rect().size) ))
        self.size=array(img.get_rect().size)
        return img

class PlaceLayer(BaseCanvasLayer):
    pass

class PlaceData(BaseCanvasData):
    dft={'name':'place','music':'','panrange':(0,0,0,0),'bg':''}
    infotypes=deepcopy(BaseCanvasData.infotypes)
    infotypes['sprite']=('name',)
    datatype='place'
    Layer=PlaceLayer

    def __init__(self,cast=None,setting=None,**kwargs):
        self.name='place'
        self.music=''
        self.bg=''
        self.panrange=(0,0,0,0)
        for i,j in BaseCanvasData.dft.iteritems():
            self.dft.setdefault(i,j)
        self.size=self.dft['size']
        super(PlaceData, self).__init__()
        #DATA ONLY
        self.renew()

    def renew(self):
        BaseCanvasData.renew(self)
        self.idx=0
        self.add(self.Layer() )
        for l in self.layers:
            l.source=self

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['music','bg','panrange']
        return BaseCanvasData.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def klassmake(self,klass,*args):
        return eval(klass)(*args)

    def __repr__(self):
        return 'Place {}'.format(self.name)

    def add(self,item,**kwargs):
        if  BaseCanvasData.add(self,item,**kwargs):
            #all below should be useless
            if item.type=='sprite':
                if kwargs.get('layer',None):
                    if not kwargs['layer'] in self.layers:
                        print 'Missing layer', kwargs['layer']
                        self.add(kwargs['layer'])
                    if not item in kwargs['layer'].items:
                        kwargs['layer'].items.append(item)
                    else:
                        print 'PlaceADD: UNEXPECTED', kwargs['layer']
                else:
                    if not item in self.layers[0].items:
                        print 'PlaceADD: UNEXPECTED', item
                        self.layers[0].items.append(item)
            return True
        return False



class PlaceView(BaseCanvasView):
    icon_types={'dft':PlaceSpriteIcon}

    def __init__(self,handler,parent=None,**kwargs):
        kwargs['handler']=handler
        self.parent=parent
        super(PlaceView, self).__init__(**kwargs)

    def get_hotspot(self,icon):
        bound= self.handler.data.get_info(icon.item,'bound')
        if bound:
            return self.handler.cast.view.get_hotspot(icon)
        else:
            return icon.rect.center

class PlaceHandler(BaseCanvasHandler):
    master=True
    name='placehandler'
    handlername='Handler'
    View=PlaceView
    Data=PlaceData

    def __init__(self,parent,**kwargs):
        BaseCanvasHandler.__init__(self,parent,**kwargs)

    @property
    def components(self):
        return ()

    def make_dependencies(self):
        self.depend.clear()
        BaseCanvasHandler.make_dependencies(self)
        deplist=()
        for c in self.components:
            c.make_dependencies()
            deplist+= (self,c),
            deplist+= (self,c.data),
            deplist+= (c,c.data),
        #deplist+=(self,self.data),
        [self.depend.add_dep(*d) for d in deplist]

    def set_data(self,data):
        BaseCanvasHandler.set_data(self,data)
        self.make_dependencies()


    def react(self,evt):
        if 'change_infos' in evt.type:
            if array( [i in evt.infos for i in ('set','source','scale') ]).any():
                target=evt.item
                self.view.icon_update(target)
        BaseCanvasHandler.react(self,evt)

    def txt_import(self,filename,**kwargs):
        data=self.Data()
        data.txt_import(filename)
        self.set_data(data)


class PlaceEditor(PlaceHandler,BaseCanvasEditor):
    name='placeeditor'
    Sprite=PlaceSprite

    def __init__(self,parent,**kwargs):
        BaseCanvasHandler.__init__(self,parent,**kwargs)

    def menu(self,*args,**kwargs):
        return BaseCanvasEditor.menu(self,*args,**kwargs)

    def bgmenu(self,*args,**kwargs):
        struct= ()
        struct+=(
            ('Edit place',lambda e=self.data: self.signal('edit',e)),
            ('Add sprite', self.add_sprite ),
            ) + BaseCanvasEditor.bgmenu(self,*args,**kwargs)+(
                )
        return struct

    def add_sprite(self,item=None,layer=None,**kwargs):
        act=self.active_layer
        if not item:
            item=self.Sprite()
            kwargs.setdefault('pos',self.view.mousepos())
        if not layer:
            layer= act#self.canvas.graph
        kwargs.setdefault('infos',{})
        kwargs['infos'].setdefault('layer',layer)
        evt=AddEvt(item,self.data,**kwargs)
        #self.canvas.add(act.Node(),pos=self.mousepos() )
        return user.evt.do(evt )


class PlaceSpritePanel(SidePanel):
    title = 'Sprite editor'
    def set_ref(self,*args,**kwargs):
        if self.ref!=args[0]:
            self.ref=args[0]
            self.make_attrs(*args)
        else:
            self.make_attrs(*args,differential=1)
        SidePanel.set_ref(self,*args,**kwargs)

    def make_attrs(self,*args,**kwargs):
        scene=self.data
        srcs=[]
        oldattrs=self.attrs[:]
        #path=database['{}_path'.format(scene.datatype)]
        path=database['scene_path']
        for d in ('common/',scene.name+'/'):
            try:
                srcs+=[d+i for i in olistdir(path+d) ]
            except:
                pass
        if os.path.isdir(path+args[0].source+'/'):
            sets=[i.split('.')[0] for i in olistdir(path+args[0].source+'/')]
        else:
            sets=[]
        self.attrs=[
                ('name','input','Name',100,{'charlimit':20,'itemwrite':True}),
                ('source','listsel','Source',300,{'values':srcs,'itemwrite':True}),
                ('scale','drag','Scale',80,{'minval':0.2,'maxval':2.,'itemwrite':True}),
            ]
        if sets:
            self.attrs+=('set','arrowsel','Set',120,{'values':sets,'itemwrite':True}),
        for a in kwargs.get('add_attrs', ()):
            done=0
            for idx,oa in enumerate(self.attrs):
                if a[0] ==oa[0]:
                    self.attrs[idx]=a
                    done=1
                    break
            if not done:
                self.attrs.append(a)
        self.attrs=tuple(self.attrs)

        if not kwargs.get('differential',False):
            self.make()
            return True
        difference= len(self.attrs) != len(oldattrs)
        optdif={}
        i=0
        while not difference and i < len(oldattrs):
            old,new=oldattrs[i],self.attrs[i]
            if old[:4]!=new[:4]:
                difference=1
            if old[4]!=new[4]:
                optdif[new[0]]=(new[4],old[4])
            i+=1
        if difference:
            self.make()
            self.renew_chgevts()
        elif optdif:
            print 'TODO:', optdif


class PlaceLayerPanel(SidePanel):
    title = 'Setting layer editor'

    def set_ref(self,*args,**kwargs):
        if self.ref!=args[0]:
            self.ref=args[0]
            self.make_attrs(*args)
        else:
            self.make_attrs(*args,differential=1)
        SidePanel.set_ref(self,*args,**kwargs)


    def make_attrs(self,*args,**kwargs):
        scene=self.data
        oldattrs=self.attrs[:]
        self.attrs=[
                ('name','input','Name',100,{'charlimit':20}),
                ('offset','array','Offset',100,{'length':2, 'charlimit':4,'allchars':'relnum','charlist':(),'typecast':int}),
                ('zoom','drag','Zoom',80,{'minval':0.2,'maxval':2.}),
                ('alpha','drag','Alpha',80,{'minval':0.,'maxval':1.}),
                ('distance','drag','Distance',80,{'minval':-1.,'maxval':1.}),
            ]
        if self.ref:
            self.attrs.append(('state','arrowsel','State',120,{'values':self.ref.states}))
        for a in kwargs.get('add_attrs', ()):
            done=0
            for idx,oa in enumerate(self.attrs):
                if a[0] ==oa[0]:
                    self.attrs[idx]=a
                    done=1
                    break
            if not done:
                self.attrs.append(a)
        self.attrs=tuple(self.attrs)
        if not kwargs.get('differential',False):
            self.make()
            return True
        difference= len(self.attrs) != len(oldattrs)
        optdif={}
        i=0
        while not (difference  or i== len(oldattrs)):
            old,new=oldattrs[i],self.attrs[i]
            if old[:4]!=new[:4]:
                difference=1
            elif old[4]!=new[4]:
                optdif[new[0]]=new[4]
            i+=1
        if difference:
            self.make()
            self.renew_chgevts()
        elif optdif:
            print 'TODO:', optdif



class PlacePanel(SidePanel):
    title = 'Place editor'
    attrs=(
        ('name','input','Title',100,{'charlimit':20}),
        ('music','listsel','Music',200,{'values':['']+sorted(olistdir(database['music_path']))}),
        ('size','array','Size',200,
            {'length':2, 'charlimit':4,'allchars':'relnum','charlist':(),'typecast':int}),
        ('panrange','array','Pan range',300,
            {'length':4, 'charlimit':4,'allchars':'relnum','charlist':(),'typecast':int}),
        ('bg','arrowsel','Background',120,{
            'values': ['None']+[i for i in olistdir(database['backgrounds']) if not
            os.path.isdir(os.path.join(database['backgrounds'],i )) ] }),
        )


class PlaceEditorUI(EditorUI):
    Editor=PlaceEditor
    SM=EditorSM

    def __init__(self,screen,scenedata,**kwargs):
        self.soundmaster = self.SM(self)
        self.game_ui=kwargs.get('game_ui',None)
        self.scene= self.Editor(self,data=scenedata)
        wintypes=kwargs.pop('wintypes',dict((  ('statusbar',lambda e,s=self:
                            StatusBar(e,menu=  [ ('Menu', s.statusmenu)] )),
                        ('sidepanel',lambda e,s=self:SidePanel(e,s.scene)),
                        ('placepanel',lambda e,s=self: PlacePanel(e,s.scene.data,itemwrite=True)),
                        ('spritepanel',lambda e,s=self: PlaceSpritePanel(e,s.scene)),
                        ('layerpanel',lambda e,s=self: PlaceLayerPanel(e,s.scene.data)),
                        ('layermenu', lambda e,s=self: LayerMenu(e,s.scene) )
                    )))
        sidetypes=kwargs.pop('sidetypes',('placepanel','spritepanel','layerpanel')) #'actorpanel','matchpanel','settingpanel'


        super(PlaceEditorUI, self).__init__(screen,None,wintypes=wintypes,sidetypes=sidetypes,**kwargs)
        self.layers.append(self.scene)

    @property
    def components(self):
        return (self.scene,)+self.scene.components

    def make_dependencies(self):
        BasicUI.make_dependencies(self)
        user.evt.set_handle(self.scene)
        self.scene.make_dependencies()
        deplist= (self,self.scene.data),
        for c in self.components:
            deplist+=(self,c),
        for d in deplist:
            self.depend.add_dep(*d)
        if self.window['statusbar']:
            self.depend.add_dep(self.window['statusbar'],user)

    def statusmenu(self):
        m=self.scene
        struct=()
        dtype=m.data.datatype
        lams=lambda: self.save_menu(dtype,m.save_to_file,default=m.data.name)
        laml=lambda: self.load_menu(dtype,m.set_from_file)
        struct+=('Save scene',lams),('Load scene',laml)
        struct +=('Play scene',lambda e=None: m.signal('start_scene')),
        lamg=lambda:m.data.txt_export(filename=m.data.name)
        lami=lambda e:m.txt_import(filename=e)
        struct+=('Export scene as text',lamg),
        struct+=('Import scene from text',lambda:self.load_menu(dtype,lami,ext='.arc.txt') ),
        if self.game_ui :
            struct+=  ('Return to game',self.return_to_game),
        else:
            struct+= ('Exit',self.return_to_title),
        return struct

    def return_to_game(self):
        fopen('.editor_last','w')
        user.set_ui(self.game_ui,False, no_launch=True )

    def return_to_title(self):
        self.scene.save_to_file('archive/last.dat')
        user.set_ui(StartMenuUI(self._screen))


    def react(self,evt):
        super(PlaceEditorUI, self).react(evt)
        if 'layermenu' in evt.type:
            self.show('layermenu')

    def keymap(self,event):
        handled=False
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_s :
                m=self.scene
                m.save_to_file(m.data.name)
                user.set_status('Saved as '+m.data.name)
                handled=True
        return handled or EditorUI.keymap(self,event)


class SettingData(PlaceData):
    pass

class OldSettingData(Data):

    name='dft_setting'
    infotypes={
        'place':('background'),
        'variable':('val',) #local variables
        }

    dft={'name':'setting','bg':None}
    bg=None
    def __init__(self):
        super(SettingData, self).__init__()
        self.type='setting'
        self.vargraph=nx.DiGraph()


    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['bg','vargraph']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

class OldSettingHandler(Handler):

    def __init__(self,parent,**kwargs):
        self.parent = parent
        self.data=kwargs.get('data',SettingData())
        self.view=kwargs.get('view',SettingView(self,parent.view))
        self.view.handler=self
        self.depend=DependencyGraph()
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

    def set_data(self,*args,**kwargs):
        Handler.set_data(self,*args,**kwargs)
        if self.data.bg:
            self.set_background(self.data.bg)

    def react(self,evt):
        if 'change' in evt.type:
            self.set_background(self.data.bg)

        return Handler.react(self,evt)

class OldSettingView(View):
    offset=(0,0)

    def __init__(self,handler,parent=None,**kwargs):
        super(SettingView, self).__init__(handler,parent,**kwargs)
        self.bg=None

    def paint(self,surface=None):
        if not surface:
            surface=self.surface
        if self.bg:
            surface.blit(self.bg,-array(self.offset))


class SettingView(PlaceView):
    def hover(self,*args):
        return False
    def event(self,*args,**kwargs):
        return False


class SettingHandler(PlaceHandler):
    View=SettingView
    def event(self,*args,**kwargs):
        return False
    def menu(self,*args,**kwargs):
        return ()
    def bgmenu(self,*args,**kwargs):
        return ()
    def spritemenu(self,*args,**kwargs):
        return ()

class SettingEditor(SettingHandler):
    pass

class SettingPlayer(SettingHandler):
    pass

