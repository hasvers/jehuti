# -*- coding: utf-8 -*-
from gam_cutscene import *


class ActsceneSprite(CutsceneSprite):
    dft={'name':'Sprite',
        'set':'default',
        'source':'common/default',
        'scale':1.,
        'bound':None, #bound data item
        'usable':'Off',
        'scripts':[],
        'desc':'',
        'mouseover':''
        }
    SpriteID=0
    def __init__(self,*args,**kwargs):
        DataItem.__init__(self,*args,**kwargs)
        ActsceneSprite.SpriteID+=1
        self.type='sprite'
        if self.name==self.dft['name']:
            self.name+=str(ActsceneSprite.SpriteID)

    def __repr__(self):
        return self.name

class ActsceneLayer(CutsceneLayer):
    dft=deepcopy(CutsceneLayer.dft)
    dft['usable']='Off'


class ActsceneData(CutsceneData):

    dft=deepcopy(CutsceneData.dft)
    dft['name']='actscene'
    infotypes=deepcopy(CutsceneData.infotypes)
    infotypes['sprite']+=('usable','scripts','desc','mouseover')
    infotypes['layer']+=('usable',)
    datatype='actscene'
    Layer=ActsceneLayer

    def __repr__(self):
        return 'Actscene {}'.format(self.name)

    def klassmake(self,klass,*args):
        return eval(klass)(*args)

class ActsceneSpriteIcon(CutsceneSpriteIcon):
    pass

    #def set_state(self,state,*args,**kwargs):
        #if state=='hover':
            #self.set_state('blur')
        #CutsceneSpriteIcon.set_state(self,state,*args,**kwargs)

    #def rm_state(self,state,*args,**kwargs):
        #if state=='hover':
            #self.rm_state('blur')
        #CutsceneSpriteIcon.rm_state(self,state,*args,**kwargs)


class ActsceneView(CutsceneView):
    icon_types={'dft':ActsceneSpriteIcon}


class ActscenePlayView(ActsceneView):

    def test_hovering(self,*args,**kwargs):
        hover=None
        for l in self.handler.data.layers[::-1]:
            if hover:
                break
            if self.handler.data.get_info(l,'usable')=='On':
                kwargs['layer']=l
                hover=ActsceneView.test_hovering(self,*args,**kwargs)
        return hover

class ActsceneHandler(CutsceneHandler):
    master=True
    name='actscenehandler'
    handlername='Handler'
    View=ActsceneView
    Data=ActsceneData
    Cast=CastSceneHandler
    Setting=SettingHandler

class ActsceneEditor(ActsceneHandler,CutsceneEditor):
    name='actsceneeditor'
    Sprite=ActsceneSprite
    Cast=CastSceneHandler
    Setting=SettingHandler

class ActscenePlayer(ActsceneHandler,CutscenePlayer):
    name='actsceneplayer'
    View=ActscenePlayView
    Cast=CastSceneHandler
    Setting=SettingHandler
    clickable=1

    def clear_scene(self):
        self.clear_phase()
        for s in self.data.sprites:
            self.view.icon[s].rm_state('disabled')
        for script in self.data.scripts:
            script.runs=0

    def start_scene(self):
        for s in self.data.sprites:
            if not self.data.get_info(s,'usable'):
                self.view.icon[s].set_state('disabled')
        pg.event.set_allowed(30)
        try:
            if self.data.music:
                user.music.play(self.data.music)
        except:
            pass

        for s in self.data.scripts:
            if s.test_cond('start'):
                self.add_phase(s)
        change=1
        while change:
            change=self.advance_phase()

    def hover(self,target):
        if ActsceneHandler.hover(self,target):
            mo= self.data.get_info(target,'mouseover')
            if mo:
                user.set_mouseover(mo)
            return 1
        return 0

    def unhover(self,**kwargs):
        if ActsceneHandler.unhover(self,**kwargs):
            user.kill_mouseover()
            return 1
        return 0

    def left_click(self,target,event=None):
        if target and not self.stack:
            scripts= self.data.get_info(target.item,'scripts')
            for scr in scripts:
                if scr.test_cond(self,event):
                    self.add_phase(scr)
        return True
    def double_click(self,target, event=None):
        return True
    def right_click(self,target,event=None):
        return False

    def bgdrag(self,rel):
        user.grab(self.view)
        self.limpan(rel)
        return 1

    def keymap(self,event):
        if event.key in (pg.K_UP,pg.K_DOWN,pg.K_LEFT,pg.K_RIGHT):
            if event.key==pg.K_UP:
                dif=(0,-2)
            elif event.key==pg.K_DOWN:
                dif=(0,2)
            elif event.key==pg.K_RIGHT:
                dif=(2,0)
            elif event.key==pg.K_LEFT:
                dif=(-2,0)
            self.limpan(dif)
            return True

    def limpan(self,rel):
        x,y=rel
        panrange=array((0,0,0,0) )
        if x<0:
            i=1
        else:
            i=0
        panrange[i]+=abs(x)
        panrange[1-i]-=abs(x)
        if y<0:
            i=1
        else:
            i=0
        panrange[2+i]+=abs(y)
        panrange[3-i]-=abs(y)
        selfpan=self.data.panrange+panrange
        settingpan=self.setting.data.panrange+panrange
        if not False in [z>=0 for z in settingpan]:
            self.setting.data.panrange=settingpan
            self.setting.pan(rel)
        if not False in [z>=0 for z in selfpan]:
            self.data.panrange=selfpan
            self.pan(rel)
    def drag(self):
        return False

class ActsceneSpritePanel(CutsceneSpritePanel):
    title = 'Sprite editor'

    def make_attrs(self,*args,**kwargs):
        kwargs.setdefault('add_attrs',())
        kwargs['add_attrs']+=(
                ('desc','input','Description',190,{'height':140,'wrap':True}),
                ('usable','arrowsel','Interactive',100,{'values':('On','Off') } ),
                ('mouseover','input','Mouseover',100,{'charlimit':100}),
                ('scripts','inputlist','Scripts',300,{'add':True,'menu':{'type':'script'}}),
            )
        return CutsceneSpritePanel.make_attrs(self,*args,**kwargs)


class ActsceneLayerPanel(CutsceneLayerPanel):
    title = 'Actscene layer editor'

    def make_attrs(self,*args,**kwargs):
        kwargs.setdefault('add_attrs',())
        kwargs['add_attrs']+=(
                ('usable','arrowsel','Interactive',100,{'values':('On','Off') } ),
            )
        return CutsceneLayerPanel.make_attrs(self,*args,**kwargs)

class ActscenePanel(CutscenePanel):
    title = 'Actscene editor'

class ActsceneEditorUI(CutsceneEditorUI):
    Editor=ActsceneEditor
    SM=CutsceneSM
    def __init__(self,screen,data,**kwargs):
        self.scene=None
        wintypes=kwargs.pop('wintypes',dict((  ('statusbar',lambda e,s=self:
                            StatusBar(e,menu=  [ ('Menu', s.statusmenu)] )),
                        ('sidepanel',lambda e,s=self:SidePanel(e,s.scene)),
                        ('actscenepanel',lambda e,s=self: ActscenePanel(e,s.scene.data,itemwrite=True)),
                        ('spritepanel',lambda e,s=self: ActsceneSpritePanel(e,s.scene)),
                        ('layerpanel',lambda e,s=self: ActsceneLayerPanel(e,s.scene.data)),
                        ('layermenu', lambda e,s=self: LayerMenu(e,s.scene) )
                    )))
        sidetypes=kwargs.pop('sidetypes',('actscenepanel','spritepanel','layerpanel'))
        super(ActsceneEditorUI, self).__init__(screen,data,wintypes=wintypes,sidetypes=sidetypes,**kwargs)

    def react(self,evt):
        if 'start_scene' in evt.type :
            scene=self.scene
            ui= ActsceneUI(self._screen,scene.data,game_ui=self.game_ui,editor_ui=self )
            ui.debug=1
            return user.set_ui(ui,False)
        super(ActsceneEditorUI, self).react(evt)

class ActsceneUI(CutsceneUI):
    Player=ActscenePlayer
    SM=CutsceneSM
