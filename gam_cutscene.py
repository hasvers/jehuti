# -*- coding: utf-8 -*-
from gam_scene import *
#from gam_cutscene_events import *

class CutsceneSprite(DataItem):
    dft={'name':'Sprite',
        'set':'default',
        'source':'common/default',
        'scale':1.,
        'bound':None, #bound data item
        }
    SpriteID=0
    def __init__(self,*args,**kwargs):
        DataItem.__init__(self,*args,**kwargs)
        CutsceneSprite.SpriteID+=1
        self.type='sprite'
        if self.name==self.dft['name']:
            self.name+=str(CutsceneSprite.SpriteID)

    def __repr__(self):
        return self.name

class CutsceneSpriteIcon(BaseCanvasIcon):
    mutable=1
    def make_surface(self,size,mod,*args,**kwargs):
        item=self.item
        iset=self.canvas.handler.data.get_info(item,'set')
        if not iset:
            iset='default'
        img = None
        for path in ('cutscene_path','actscene_path','scene_path'):
            path = database[path]
            try:
                img=image_load(path+item.source+'/'+iset+'.png')
            except:
                try:
                    img=image_load(path+item.source)
                except:
                    pass
        if img is None:
            img=image_load(database['scene_path'] +'/default/default.png')
        img=img.convert_alpha()
        img=pg.transform.smoothscale(img, tuple(int(x*item.scale) for x in array(img.get_rect().size) ))
        self.size=array(img.get_rect().size)
        return img


    def get_hotspot(self,*args,**kwargs):
        if kwargs.get('balloon',False):
            return self.canvas.get_hotspot(self)
        return UI_Icon.get_hotspot(self,*args,**kwargs)

class CutsceneLayer(BaseCanvasLayer):
    pass

class CutsceneData(PlaceData):
    #CutScene contains data from a Cast and a Setting
    #(so that they can be modified by cutscene events)

    dft=deepcopy(PlaceData.dft)
    dft['name']='cutscene'
    infotypes=deepcopy(PlaceData.infotypes)
    infotypes['sprite']=('name','bound')
    datatype='cutscene'
    Layer=CutsceneLayer

    def __init__(self,cast=None,setting=None,**kwargs):
        super(CutsceneData, self).__init__()
        #DATA ONLY
        self.cast=cast
        self.setting=setting

    def renew(self):
        BaseCanvasData.renew(self)
        self.scripts=[]
        self.queue=[]
        self.idx=0
        self.add(self.Layer() )
        for l in self.layers:
            l.source=self

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['cast','setting','scripts']
        return PlaceData.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def klassmake(self,klass,*args):
        return eval(klass)(*args)

    def __repr__(self):
        return 'Cutscene {}'.format(self.name)

class CutsceneView(PlaceView):
    icon_types={'dft':CutsceneSpriteIcon}

    #@property
    #def bg(self):
        #return self.handler.setting.view.paint()

class CutsceneHandler(PlaceHandler,SceneHandler):
    master=True
    name='cutscenehandler'
    handlername='Handler'
    View=CutsceneView
    Data=CutsceneData
    Cast=CastSceneHandler
    Setting=SettingHandler

    def __init__(self,parent,**kwargs):
        BaseCanvasHandler.__init__(self,parent,**kwargs)
        SceneHandler.__init__(self,**kwargs)
        self.make_bindings()


    @property
    def components(self):
        return (self.cast,self.setting)

    def set_data(self,data):
        BaseCanvasHandler.set_data(self,data)
        self.cast.clear()
        self.cast.set_data(data.cast)
        self.setting.set_data(data.setting)
        self.make_dependencies()
        self.make_bindings()

    def make_bindings(self):
        for s in self.data.sprites:
            bound=self.data.get_info(s,'bound')
            if not bound:
                continue
            if bound in self.cast.actors:
                self.bind_sprite(s,bound)

    def bind_sprite(self,sprite,actor):
        self.cast.view.icon[actor]=self.view.icon[sprite]
        if self.data.get_info(sprite,'bound')!=actor:
            self.data.set_info(sprite,'bound',actor)

    def txt_import(self,filename,**kwargs):
        data=self.Data(LocCastData(),SettingData())
        data.txt_import(filename)
        print 'Still a problem with adding layer', data.layers, [l.items for l in data.layers]
        self.set_data(data)

class CutsceneEditor(PlaceEditor,SceneEditor,CutsceneHandler):
    name='cutsceneeditor'
    Sprite=CutsceneSprite
    Setting=SettingEditor
    Cast=CastSceneHandler

    def __init__(self,parent,**kwargs):
        BaseCanvasHandler.__init__(self,parent,**kwargs)
        SceneEditor.__init__(self)
        self.make_bindings()

    def menu(self,*args,**kwargs): #useful because multiple inheritance dangerous
        return PlaceEditor.menu(self,*args,**kwargs)

    def bgmenu(self,*args,**kwargs):
        struct= ()
        struct+=(
            ('Edit scene',lambda e=self.data: self.signal('edit',e)),
        )
        #lam=lambda: self.parent.load_menu('cast',self.cast.add_actor_from_file,new=self.cast.new_actor)
        struct+=(
            ('Edit setting',lambda e=self.setting.data: self.signal('edit',e)),
            ('Add sprite', self.add_sprite ),
            ) + BaseCanvasEditor.bgmenu(self,*args,**kwargs)
        struct+=SceneEditor.menu(self,*args,**kwargs)
        return struct

    def spritemenu(self,sprite,**kwargs):
        struct=BaseCanvasEditor.spritemenu(self,sprite,**kwargs)
        bound=self.data.get_info(sprite,'bound')
        if not bound:
            substruct=tuple( (a.name,lambda tgt=sprite,act=a: self.bind_sprite(tgt,act ) )
                 for a in self.cast.actors)
            if substruct:
                struct+=('Bind to actor',lambda s=substruct: self.parent.float_menu(substruct) ),
        return struct


class CutscenePlayer(CutsceneHandler,PhaseHandler):
    clickable=0
    Setting=SettingPlayer
    Cast=CastSceneHandler

    def __init__(self,parent,**kwargs):
        BaseCanvasHandler.__init__(self,parent,**kwargs)
        SceneHandler.__init__(self)
        PhaseHandler.__init__(self)
        self.make_bindings()

    def clear_scene(self):
        self.clear_phase()
        self.view.actions['hover']=True
        self.view.actions['select']=True
        self.view.block_actions=False
        for script in self.data.scripts:
            script.runs=0

    def start_scene(self):
        self.view.block_actions=True
        self.view.actions['hover']=False
        self.view.actions['select']=False
        pg.event.set_allowed(30)
        try:
            if self.data.music:
                user.music.play(self.data.music)
        except:
            pass

        for s in self.data.scripts:
            if s.test_cond('start'):
                self.add_phase(s)
                #print s, [(c,c.state) for c in s.all_children()]
#                s.run(self)
        change=1
        while change:
            change=self.advance_phase()


    def event(self,event,**kwargs):
        handled= CutsceneHandler.event(self,event,**kwargs)
        if event.type==30 and not user.paused:
            self.time+=1
        #if not handled:
            self.advance_phase()
        return handled


    def left_click(self,target,event=None):
         return True
    def double_click(self,target, event=None):
        return True
    def right_click(self,target,event=None):
        return False
    def mousewheel(self,target,event):
        if event.button==4:
            d=1
        elif event.button==5:
            d=-1
        return False
    def bgdrag(self,rel):
        #self.pan(rel)
        return False
    def drag(self):
        return False

class CutsceneSM(BasicSM):
    def receive_signal(self,signal,*args,**kwargs):
        sgn=signal.type
        if 'set_' in sgn:
            return self.play('load')

class CutsceneSpritePanel(PlaceSpritePanel):
    title = 'Sprite editor'

    def make_attrs(self,*args,**kwargs):
        scene=self.data
        kwargs.setdefault('add_attrs',())
        kwargs['add_attrs']+=(
                ('bound','listsel','Binding',100,{'values':[None]+scene.cast.actors }),
            )
        return PlaceSpritePanel.make_attrs(self,*args,**kwargs)


class CutscenePanel(SidePanel):
    title = 'Cutscene editor'
    attrs=deepcopy(PlacePanel.attrs)
    attrs+= ('scripts','inputlist','Scripts',300,{'add':True,'menu':{'type':'script'}}),

class CutsceneLayerPanel(PlaceLayerPanel):
    title = 'Cutscene layer editor'

class CutsceneEditorUI(PlaceEditorUI,SceneUI):
    Editor=CutsceneEditor
    SM=CutsceneSM
    def __init__(self,screen,scenedata,**kwargs):
        self.soundmaster = self.SM(self)
        self.scene=scene = self.Editor(self,data=scenedata)
        SceneUI.__init__(self,**kwargs)
        if self.statusmenu():
            smenu=[('Menu',self.statusmenu)]
        else:
            smenu=False
        wintypes=kwargs.pop('wintypes',dict((  ('statusbar',lambda e: StatusBar(e,menu=smenu)),
                        ('sidepanel',lambda e,t=scene:SidePanel(e,t)),
                        ('placepanel',lambda e,t=scene.data: SettingPanel(e,t,itemwrite=True)),
                        ('cutscenepanel',lambda e,t=scene.data: CutscenePanel(e,t,itemwrite=True)),
                        ('spritepanel',lambda e,t=scene.data: CutsceneSpritePanel(e,t)),
                        ('layerpanel',lambda e,t=scene.data: CutsceneLayerPanel(e,t)),
                        ('layermenu', lambda e, t=scene : LayerMenu(e,t) )
                    )))
        sidetypes=kwargs.pop('sidetypes',('placepanel','cutscenepanel','spritepanel','layerpanel')) #'actorpanel','matchpanel','settingpanel'

        EditorUI.__init__(self,screen,None,wintypes=wintypes,sidetypes=sidetypes,**kwargs)
        self.layers.append(self.scene)


    def input_menu(self,typ,output_method,**kwargs):
        if typ=='script':
            return self.script_maker(output_method,**kwargs)
        elif typ[0]=='scriptcond':
            return self.script_cond_maker(output_method,typ[1],**kwargs)
        elif typ[0]=='scripteffect':
            return self.script_effect_maker(output_method,typ[1],**kwargs)
        else :
            return super(CutsceneEditorUI, self).input_menu(typ,output_method,**kwargs)

    def old_script_cond_maker(self,output_method,**kwargs):
        klass=SceneScriptCondition
        ref=kwargs.pop('val',None)
        if not isinstance(ref,klass):
            ref=klass()
        flist=(
            ('name','input',{'legend':'Name','width':200}),
            ('typ','toggle',{'templates':ref.templates}),
            )
        kwargs.setdefault('title','Script condition:')
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)

    def script_maker(self,output_method,**kwargs):
        test=SceneScriptCondition()
        condtyps=sorted(test.templates(handler=self.scene))
        condtyps= [(test.type,i) for i in condtyps]
        test=SceneScriptEffect()
        efftyps=sorted(test.templates(handler=self.scene))
        efftyps= [(test.type,i) for i in efftyps]
        flist=(
            ('name','input',{'legend':'Name','width':200}),
            ('iter','arrowsel',{'values':('always',0,1,2,3,4)}),
            ('conds','inputlist',{'legend':'Conditions','width':400,'add':True,'menu':{'type':condtyps}}),
            ('effects','inputlist',{'legend':'Effects','width':400,'add':True,'menu':{'type':efftyps}}),
            )
        kwargs.setdefault('title','Script:')
        self.maker_menu(flist,output_method,Script,**kwargs)


    def script_cond_maker(self,output_method,typ,**kwargs):
        klass=SceneScriptCondition
        ref=kwargs.pop('val',None)
        if not isinstance(ref,klass):
            ref=klass()
        ref.typ=typ
        flist=(
            ('name','input',{'legend':'Name','width':200}),
            ('typ','toggle',{'templates':ref.templates})
            )
        kwargs.setdefault('title','Script condition: {}'.format(typ))
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)

    def script_effect_maker(self,output_method,typ,**kwargs):
        klass=SceneScriptEffect
        ref=kwargs.pop('val',None)
        if not isinstance(ref,klass):
            ref=klass()
        ref.typ=typ
        flist=(
            ('name','input',{'legend':'Name','width':200}),
            ('typ','toggle',{'templates':ref.templates}),
            )
        kwargs.setdefault('title','Script effect: {}'.format(typ))
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)


    def react(self,evt):
        super(CutsceneEditorUI, self).react(evt)

        if 'start_scene' in evt.type :
            scene=self.scene
            #views={'canvas':match.canvas,'cast':match.cast.view,'setting':match.setting.view}
            #for v in views.values()+[match.canvas.handler]:
                #try:
                    #v.unhover()
                    #v.unselect()
                #except:
                    #pass
            ui= CutsceneUI(self._screen,scene.data,game_ui=self.game_ui ,editor_ui=self)
            ui.debug=1
            return user.set_ui(ui,False)

    def keymap(self,event):
        handled=False
        return handled or PlaceEditorUI.keymap(self,event)


class CutsceneUI(BasicUI,SceneUI):
    debug=0
    Player=CutscenePlayer
    SM=CutsceneSM
    def __init__(self,screen,scenedata,**kwargs):
        self.soundmaster = self.SM(self)
        self.scene= self.Player(self,data=scenedata)
        SceneUI.__init__(self,**kwargs)
        temp={'viewables':('floatmenu','menu','balloon','dialbox') ,'floatmenu':True,'menu':True,'balloon':'reverse','dialbox':True}
        BasicUI.__init__(self,screen,template=temp,**kwargs)
        self.layers.append(self.scene)
        #if self.game:
            #self.layers.append(self.game)

    def launch(self):
        self.make_dependencies()
        self.scene.start_scene()

    @property
    def components(self):
        return (self.scene,)

    def make_dependencies(self):
        BasicUI.make_dependencies(self)
        user.evt.set_handle(self.scene)
        self.scene.make_dependencies()
        deplist=(
            (self,self.scene.cast),
            (self,self.scene),
            (self,self.scene.data),
        )
        for d in deplist:
            self.depend.add_dep(*d)

    def general_menu(self,event=None):
        struct=()
        if self.editor_ui:
            struct +=( ('Return to editor',self.scene.return_to_editor ), )
        elif self.game_ui:
            struct+=tuple(self.game_ui.game.menu(event))
        if struct:
            self.float_menu(struct,oneshot=True)
        return False

    def go_editor(self):
        user.music.stop()
        return user.set_ui(self.editor_ui)

    def react(self,evt):
        source=evt.source
        if self.name==source:
            return False
        sgn=evt.type
        if 'return_to_editor' in sgn :
            return self.go_editor()
        super(CutsceneUI, self).react(evt)
        return False



    def keymap(self,event):
        handled=False
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_p:
                return user.screenshot()

            if pg.key.get_pressed()[pg.K_LALT] and event.key==pg.K_v and database['edit_mode']:
                return user.trigger_video()
        if self.game_ui:
            return handled or self.game_ui.game.keymap(event)
        else:
            return handled