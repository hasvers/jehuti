# -*- coding: utf-8 -*-

from gam_cast_view import *




class CastHandler(Handler):
    name='casthandler'

    def __init__(self,parent,**kwargs):
        self.parent = parent
        self.depend=DependencyGraph()
        self.data=kwargs.get('data',LocCastData())
        self.view=kwargs.get('view',CastView(self,parent.view))
        self.view.handler=self

    @property
    def actors(self):
        return self.data.actors

    def clear(self):
        self.depend=DependencyGraph()
        self.make_dependencies()
        self.view.renew()
        self.data.renew()
        self.upd_actors()

    def renew(self):
        self.upd_actors()

    def change_infos(self,target,**kwargs):
        eph=kwargs.pop('invisible',False)
        evt=ChangeInfosEvt(target,self.data,**kwargs)
        return user.evt.do(evt,self,None,eph)

    def react(self,evt):
        if 'change' in evt.type or 'rem_info' in evt.type:
            target=evt.item
            if 'portrait' in evt.infos:
                self.icon_update(target)
            self.hud_update(target)
        if 'add' in evt.type:
            self.upd_actors()
        if 'hud' in evt.type:
            if 'show' in evt.type:
                self.view.hud_event('show',*evt.args)
            if 'hide' in evt.type:
                self.view.hud_event('hide',*evt.args)
            if 'anim' in evt.type:
                self.view.hud_event('anim',*evt.args)

    def icon_update(self,target):
        icon=self.view.icon[target]
        icon.make_faces()
        self.view.upd_actors()

    def hud_update(self,target=None):
        if target == None:
            for act in self.actors:
                self.hud_update(act)
            return True
        if not target in self.view.hud:
            return
        hud = self.view.hud[target]
        infos={}
        infos.update(target.dft)
        infos.update(self.get_info(target))
        txt=infos['name']
        hud.txt.set_contents([txt])
        for c in hud.children:
            if c!= hud.txt:
                c.create(self.view.group)

    def event(self,*args):
        return self.view.event(*args)
        return False


    def add_actor(self,actor,**kwargs):
        if actor in self.data.actors:
            return False
        evt=AddEvt(actor,self.data,**kwargs)
        user.evt.do(evt,self)

    def upd_actors(self):
        for actor in tuple(self.view.icon.keys()) :
            if not actor in self.data.actors :
                self.view.rem_actor(actor)

        self.view.upd_actors()
        self.hud_update()

    def rem_actor(self,actor):
        self.signal('actor_deleted',actor)
        self.data.remove(actor)
        self.upd_actors()

    def new_actor(self):
        print 'Creating a new actor'
        actor =Actor()
        evt=AddEvt(actor,self.data)
        if user.evt.do(evt,self):
            self.upd_actors()

    def select(self,actor):
        if not self.view.icon[actor].is_selected:
            UI_Widget.select(self.view,self.view.icon[actor])
        self.signal('select',actor,inverse='unselect')

    def label(self,actor,info_type=False):
        if info_type=='hover':
            info_type=False
        infos=self.data.get_info(actor)
        if info_type:
            try :
                txt=infos[info_type]
            except:
                txt=infos['name']
        else :
            txt=infos['name']
            for i,j in actor.dft_names.iteritems():
                if i!='name':
                    txt += ' | '+j +': ' +unicode(infos[i])
        return txt

class CastEditor(CastHandler):

    def __init__(self,*args,**kwargs):
        CastHandler.__init__(self,*args,**kwargs)

    def menu(self,event=None):
        tmp= self.view.hovering
        struct=()
        if tmp:
            actor=tmp.actor
        else:
            return struct
        if not ergonomy['edit_on_select']:
            struct +=( ('Edit',lambda e=actor: self.signal('edit',e)), )

        struct+= ('Remove',lambda e=actor: self.rem_actor(e)),
        return struct


class CastPlayer(CastHandler):
    def __init__(self,*args,**kwargs):
        CastHandler.__init__(self,*args,**kwargs)
        assert isinstance(self.data,CastState)
            #print 'CastPlayer; leftover problem'
            #self.data=CastState(parent=self.data,rule='all')

    @property
    def rules(self):
        self.parent.rules


    def label(self,actor,info_type=False):
        if info_type=='hover':
            return u"Consider {}'s mental state.".format(self.data.get_info(actor,'name'))
        infos={}
        infos.update(actor.dft)
        infos.update(self.get_info(actor))
        if info_type:
            try :
                txt=infos[info_type]
            except:
                txt=infos['name']
        else :
            oinf = self.data.get_info(self.parent.active_player)
            txt=infos['name'] +' '+ str(infos['face'])+' '+str(infos['terr'])
            aid=actor.trueID
            if aid in oinf['prox']:
                 txt+= ' '+str(oinf['prox'][aid])
        return txt

    def set_active(self,actor):
        for act in self.actors:
            icon=self.view.icon[act]
            if act!= actor:
                icon.rm_state('disabled')
                icon.set_state('inactive')
            else:
                icon.set_state('idle')
                #icon.set_state('disabled')
            icon.rect.bottom=self.view.parent.rect.bottom
            self.hud_update(act)

    def react(self,evt):
        if 'set_player' in evt.type:
            self.hud_update()
            #self.view.hud[evt.args[0]].set_anim('oscillate')
            #self.view.icon[evt.args[0]].set_anim('blink')

        return CastHandler.react(self,evt)

    def menu(self,event=None):
        tmp= self.view.hovering
        struct=()
        if tmp:
            actor=tmp.actor
        else:
            return struct
        if actor!=self.parent.active_player:
            if not database['demo_mode']:
                struct +=( ('Speech act',lambda e=actor: self.signal('speechact',e,affects=self.data)), )
            else:
                if not self.parent.stack:
                    struct +=( ('Analyze',lambda e=actor: self.analyze(self.parent.active_player,e)), )
            #for evt in self.parent.queue: #TODO: FTA repair
                #if evt.actor==self.parent.active_player and evt.effects:
                    #struct +=( ('Repair',lambda e=actor: self.signal('repair',e)), )
                    #break
        return struct


class CastSceneHandler(CastHandler):

    def __init__(self,parent,**kwargs):
        CastHandler.__init__(self,parent,**kwargs)
        self.view=kwargs.get('view',CastSceneView(self,parent.view))

    def hover(self,sprite):
        bound=self.parent.get_info(sprite,'bound')
        if not bound:
            return 0
        return CastHandler.hover(self,bound)

    def select(self,sprite):
        return 0
