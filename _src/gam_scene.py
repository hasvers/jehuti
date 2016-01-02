# -*- coding: utf-8 -*-

from gam_phase import *
from gam_cast import *
from gam_place import *


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
        #self.cast.data.add_context(game.world)
        #self.cast.upd_actors()

    def unplug_game(self):
        pass
        #self.cast.data.rem_context(game.world)

    def import_actor(self,act,source):
        self.cast.add_actor(act,infos={'exporter':source})
        #do prox

    def import_setting(self,data):
        self.setting.set_data(data)
        #do prox

    def return_to_editor(self):
        if hasattr(self,'clear_scene'):
            self.clear_scene()
        user.music.stop()
        self.signal( 'return_to_editor',affects=user)

class SceneEditor(SceneHandler):


    def menu(self,*args,**kwargs):
        struct=()
        srcs= self.game.get_sources_for(self.data,'character')
        exactors=[]
        if srcs:
            exactors+=[(c,c.actor) for c in srcs]
        if exactors:
            flist=tuple( (act.name, lambda a=act,s=src:self.import_actor(a,s) )
                 for src,act in exactors)
            struct+=('Import actor',lambda s=struct,f=flist:user.ui.float_menu(f) ),
        places= self.game.get_sources_for(self.data,'place')
        if places:
            flist2=tuple( (p.name, lambda sc=p:self.import_setting(sc) )
                 for p in places)
            struct+=('Import setting',lambda s=struct,f=flist2:user.ui.float_menu(f) ),

        return struct