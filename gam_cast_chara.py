# -*- coding: utf-8 -*-

from gam_cast import *
from gam_match_gui import *



class CharacterData(Data):
    #Actor+Fundamental belief graph

    dft={'name':'Character','scripts':[],'actor':None}
    datatype='character'

    def __init__(self,actor,graph,**kwargs):
        self.name='character'
        self.scripts=[] #private scripts
        self.variables=[] #private variables
        super(CharacterData, self).__init__()

        self.actor=actor
        self.graph=graph
        self.belief=graph.Subgraph(graph,rule='all')
        self.belief.owner=actor
        #self.actorsubgraphs: potentially, keep knowledge of what X knows that Y knows?

    def renew(self):
        Data.renew(self)
        self.actor=Actor()
        graph=self.graph=MatchGraph()
        self.belief=graph.Subgraph(graph,rule='all')
        self.belief.owner=actor
        self.scripts=[]

    def all_scripts(self):
        return self.scripts+ list(fl for k,l in self.graph.infos.iteritems()
            for fl in l.get('cflags',() ) if isinstance(fl,CFlag))

    def klassmake(self,klass,*args):
        return eval(klass)(*args)

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['graph','actor','scripts']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def __repr__(self):
        return 'CharacterData {}'.format(self.name)



class CharaCastHandler(CastHandler):
    def menu(self,event=None):
        tmp= self.view.hovering
        struct=()
        if tmp:
            actor=tmp.actor
        else:
            return struct
        struct +=( ('Edit',lambda e=actor: self.signal('edit',e)), )
        return struct


class CharacterEditor(MatchEditor):
    master=True
    name='CharacterEditor'
    handlername='Editor'

    @property
    def actors(self):
        return self.data.cast.actors
    @property
    def graph(self):
        return self.data.graph

    def __init__(self,parent=None,**kwargs):
        self.parent=parent
        widgets=kwargs.get('view',{})
        self.depend=DependencyGraph()

        data=kwargs.pop('data',False)
        if isinstance(data,basestring):
            self.data=CharacterData #only to communicate datatype to function
            self.set_from_file(data,initial=True)
        else:
            self.data=data

        graph=self.data.graph
        self.view=widgets.get('belief',MatchView(self,parent))
        self.canvas=widgets.pop('canvas',LogicCanvas(graph=graph))
        self.canvas.set_layer(self.data.belief)
        if self.parent:
            size  =parent.screen.get_rect().size
        else :
            size=user.screen.get_rect().size
        self.view.rect.size=size
        cast=CastData()
        cast.add(self.data.actor)
        self.cast=CharaCastHandler(self,data=cast)
        self.view.children.append(self.cast.view)
        self.canvas.set_handler(LogicCanvasEditor(self.canvas,self.view,size))
        self.view.children.append(self.canvas.handler)

        self.ruleset=LogicRuleset(self.data)
        self.cast.upd_actors()
        self.canvas.dft_graph_states['idle']='ghost'
        self.canvas.set_layer(self.canvas.graph)

    @property
    def components(self):
        return (self.canvas.handler,self.cast)

    def renew_graph(self):
        if not actor:
            self.del_actorgraphs()
            self.canvas.new_graph(attr)
            self.make_actorgraphs()
            self.canvas.assess_itemstate()
            return
        sub = self.data.actorgraph[actor]
        sub.renew()
        sub.name=self.cast.get_info(actor,'name')
        rule = lambda e,a=actor:self.ruleset.actor_should_know(a,e)
        sub.import_from_parent(rule=rule)
        self.canvas.assess_itemstate()
#        self.signal('canvas_assess')


    def txt_import(self,filename,**kwargs):
        data=CharacterData(Actor(),MatchGraph())
        data.txt_import(filename)
        self.set_data(data)

    def set_data(self,data):
        self.data=data
        self.canvas.set_graph(data.graph)
        self.cast.clear()
        cast=CastData()
        cast.add(self.data.actor)
        self.cast.set_data(cast)
        self.ruleset.data=data
        self.make_dependencies()

    def react(self,evt):
        Handler.react(self,evt)
        source=evt.source
        if self.name==source:
            return False
        sgn=evt.type
        if (hasattr(evt,'item') and isinstance(evt.item,Actor)) or (source and 'cast' in source) :
            if 'unselect' in sgn  :
                self.canvas.set_layer(self.data.graph)
            elif 'select' in sgn :
                self.canvas.set_layer(self.data.belief)


    def menu(self,event):
        struct=()
        for l in (self.cast,self.canvas.handler)  :
            struct+=tuple(l.menu(event))
        return struct


class CharacterEditorUI(MatchEditorUI,SceneUI):
    CanvasEditor=MatchCanvasEditor
    def __init__(self,screen,data,**kwargs):
        self.soundmaster = EditorSM(self)
        self._screen=screen
        views=kwargs.get('matchview',{})
        self.scene = scene = CharacterEditor(self,data=data,view=views)
        SceneUI.__init__(self,**kwargs)
        if self.statusmenu():
            smenu=[('Menu',self.statusmenu)]
        else:
            smenu=False
        wintypes=kwargs.pop('wintypes',dict((  ('statusbar',lambda e: StatusBar(e,menu=smenu)),
                        ('nodelist',lambda e,t=scene.canvas.handler:NodeList(e,t)),
                        ('sidepanel',lambda e,t=scene.canvas:SidePanel(e,t)),
                        ('nodepanel',lambda e,t=scene.canvas: MatchNodePanel(e,t)),
                        ('linkpanel',lambda e,t=scene.canvas: MatchLinkPanel(e,t)),
                        ('actorpanel',lambda e,t=scene.cast: ActorPanel(e,t)),
                    )))
        sidetypes=kwargs.pop('sidetypes',('nodepanel','linkpanel','actorpanel'))
        super(MatchEditorUI, self).__init__(screen,None,wintypes=wintypes,sidetypes=sidetypes,**kwargs)
        self.layers.append(scene)

    def react(self,evt):
        super(MatchEditorUI, self).react(evt)


    def statusmenu(self):
        m=self.scene
        lams=lambda: self.save_menu('cast',m.save_to_file,default=m.data.name)
        newmatch=lambda :self.graph_maker(lambda e: m.renew(graph=e))
        laml=lambda: self.load_menu('cast',m.set_from_file,new=newmatch)
        struct=('Save character',lams),('Load character',laml)
        lamg=lambda:m.data.txt_export(filename=m.data.name)
        lami=lambda e:m.txt_import(filename=e)
        struct+=('Renew graph',lambda :self.graph_maker(lambda e: m.renew_graph(None,e))),
        struct+=('Export character as text',lamg),
        struct+=('Import character from text',lambda:self.load_menu('match',lami,ext='.arc.txt') ),
        if self.game_ui :
            #game=self.game_ui.game
            #lams=lambda: self.save_menu('game',game.save_to_file,default=game.data.name)
            #struct+= (('Save game',lams),
            struct+=('Return to game',self.return_to_game),
        else:
            struct+= ('Exit',lambda: self.confirm_menu(self.return_to_title,pos='center',
                legend='Exit to title screen?') ),
        return struct

    def keymap(self,event):
        handled=False
        return handled or MatchEditorUI.keymap(self,event)