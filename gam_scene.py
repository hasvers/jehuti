# -*- coding: utf-8 -*-

from gam_phase import *
from gam_cast import *
from gam_setting import *


#Scene is the Urclass of Match, Cutscene and Actscene

class SceneUI(object):
    game_ui=None
    editor_ui=None
    def __init__(self,*args,**kwargs):
        self.game_ui=kwargs.get('game_ui',None)
        self.editor_ui=kwargs.get('editor_ui',None)
        if self.game_ui:
            self.scene.plug_game(self.game_ui.game)


class SceneHandler(Handler):
    name='scenehandler'
    Setting=SettingHandler
    Cast=CastHandler

    def __init__(self,**kwargs):
        kwargs['data']={'cast':self.data.cast,'setting':self.data.setting}
        handlers=kwargs.get('handlers',{'setting':self.Setting,'cast':self.Cast})
        self.make_children_handlers(('setting','cast'),handlers,**kwargs )


    def plug_game(self,game):
        self.game=game
        fname=self.data.filename()
        if '_state' in fname:
            fname=self.data.parent.filename()
        links=game.context.get(fname,None)
        if not links:
            return
        concast=CastData()
        settings=[]
        for l in links:
            n2 = [p for p in l.parents if p.data!=fname][0]
            data=game.loaded[n2.data]
            if hasattr(data,'actor'):
                concast.add(data.actor)
            if data.datatype=='place':
                settings.append(data)
        self.cast.data.add_context(concast)
        self.cast.upd_actors()
        if settings:
            self.setting.set_data(settings[0])

    def unplug_game(self):
        self.cast.data.contexts=()

    def import_actor(self,act):
        self.cast.add_actor(act)
        #do prox

    def return_to_editor(self):
        if hasattr(self,'clear_scene'):
            self.clear_scene()
        user.music.stop()
        self.signal( 'return_to_editor',affects=user)

class SceneEditor(SceneHandler):


    def menu(self,*args,**kwargs):
        struct=()
        exactors=[c.context_origin.actors for c in self.data.cast.contexts if hasattr(c,'actors')]
        exactors=[a for l in exactors  for a in l if not True in [a.truename==a2.truename for a2 in self.cast.actors]]
        if exactors:
            flist=tuple( (a.name, lambda act=a:self.import_actor(act) )  for a in exactors)
            struct+=('Import actor',lambda s=struct:user.ui.float_menu(flist) ),

        return struct