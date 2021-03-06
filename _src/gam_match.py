# -*- coding: utf-8 -*-
from gam_rules import *
from gam_canvas import *
from gam_scene import *
from gam_ai import *
from gam_graph_generator import *
from gam_scene import *


#Data structures and Editor handler for rhetorical match

class MatchData(Data):
    #MatchData contains data from a Graph, a Cast and a Setting models
    #it adds actor belief graphs and other interactions between the three components

    dft={'name':'Match','scripts':[],'music':''}
    datatype='match'

    def __init__(self,graph,cast,setting,**kwargs):
        self.name='match'
        self.music=''
        self.scripts=[]
        super(MatchData, self).__init__()

        #DATA ONLY
        self.graph=graph
        self.cast=cast
        self.setting=setting
        self.renew()

    @property
    def components(self):
        return (self.graph,self.cast,self.setting)

    def renew(self):
        Data.renew(self)
        self.scripts=[]
        self.actorgraph=DataDict()
        self.make_actorgraphs()

    def make_actorgraphs(self,**kwargs):
        #print 'Mk Actorgraph',self.trueID
        tmp=list(self.actorgraph.keys())
        for actor in self.cast.actors:
            aid=actor
            if not aid in tmp:
                rule=kwargs.pop('rule','subt<'+str(actor.subt))
                sub=self.actorgraph[aid]=MatchGraph.Subgraph(self.graph)
                sub.owner=aid
                sub.name=self.cast.get_info(actor,'name')
                sub.import_from_parent(rule=rule)
            else:
                tmp.remove(aid)
        for aid in tmp:
            del self.actorgraph[aid]

    def all_scripts(self):
        return set(self.scripts)#+ list(fl for j in self.actorgraph.values()
           # for k,l in j.infos.iteritems() for fl in l.get('cflags',() ) if isinstance(fl,CFlag)))

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        for c in ('add','init'):
            kwargs.setdefault(c+'_param',[])
        kwargs['add_param']+=['graph','cast','setting','scripts','actorgraph','music']
        kwargs['init_param']+=['graph','cast','setting']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def txt_import(self,filename):
        tmp= Data.txt_import(self,filename)
        return tmp

    def __str__(self):
        return 'MatchData {}'.format(self.name)

class MatchState(MatchData):

    def __init__(self,parent,**kwargs):
        self.name='matchstate'
        self.music=''
        self.scripts=[]
        Data.__init__(self)
        self.parent=parent
        pg=parent.graph
        self.graph=pg.__class__()
        self.graph.import_from(pg,rule='all',infos=pg.infos)
        self.graph.pos=parent.graph.pos
        self.cast=CastState(parent=parent.cast,rule='all')
        self.setting=parent.setting
        self.renew()
        self.music=parent.music
        self.name=parent.name+'_state'
        self.scripts=[shallow_nested(s,1) for s in parent.scripts]
        self.turn=1
        self.time_left=1
        self.time_allowance=1
        self.active_region=((0,0),0) #barycenter and radius


    def make_actorgraphs(self,**kwargs):
        #print 'Mk State Actorgraph, parent:', self.parent.actorgraph, self.parent.trueID
        for actor in self.cast.actors:
            aid=actor.trueID
            par=self.parent.actorgraph[aid]
            sub=self.actorgraph[aid]=MatchGraph.Subgraph(self.graph)
            sub.owner=aid
            sub.name=self.cast.get_info(actor,'name')
            sub.import_from(par,rule='all',infos=par.infos)
            #print 'Mk State Actorgraph infos',sub.infos

    def renew(self):
        MatchData.renew(self)
        self.actorsubgraphs=DataDict()#sparsemat(False)
        self.reactree=nx.DiGraph()
        self.convgraph=None

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['actorsubgraphs','convgraph',
            'reactree','turn','time_left','time_allowance','active_region']
        return MatchData.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def __str__(self):
        return 'MatchState {}'.format(self.name)


class MatchView(View):
    rect=pgrect.Rect((0,0),graphic_chart['screen_size'])

class MatchHandler(SceneHandler):
    master=True
    name='matchhandler'
    handlername='Handler'

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
            self.data=MatchData
            self.set_from_file(data,initial=True)
        else:
            self.data=data
        if self.data:
            kwargs['data']={'cast':self.data.cast,'setting':self.data.setting}
            graph=self.data.graph
        else :
            graph=None

        self.view=widgets.get('match',MatchView(self,parent))#size=parent.screen.get_rect().size)
        self.canvas=widgets.pop('canvas',MatchCanvas(graph=graph))
        if self.parent:
            size  =parent.screen.get_rect().size
        else :
            size=user.screen.get_rect().size
        self.view.rect.size=size

        handlers={i:eval(i.capitalize()+self.handlername) for i in ('setting','cast')}
        self.make_children_handlers(('setting','cast'),handlers,**kwargs )
        self.canvas.set_handler(eval('MatchCanvas'+self.handlername)(self.canvas,self.view,size,
            **dict((k,kwargs[k]['canvas']) for k in kwargs if 'canvas' in kwargs[k])  ) )
        self.view.children.insert(1,self.canvas.handler)
        self.ruleset=MatchRuleset(self.data)
        if not self.data:
            self.data=MatchData(self.canvas.graph,self.cast.data,self.setting.data)

        self.cast.upd_actors()
        self.canvas.dft_graph_states['idle']='ghost'
        self.canvas.set_layer(self.canvas.graph)

        self.textmaker=TextBase()

    @property
    def components(self):
        return (self.canvas.handler,self.cast,self.setting)

    def event(self,event,**kwargs):
        if self.view.event(event,**kwargs):
            return True
        if event.type == pg.MOUSEBUTTONDOWN and 0:
            if event.button==3:
                self.call_menu(self.menu(event))
                return True
        return False

    def make_dependencies(self):
        self.depend.clear()
        deplist=()
        for c in self.components:
            c.make_dependencies()
            deplist+= (self,c),
            deplist+= (self,c.data),
        deplist+=(self,self.data),

        [self.depend.add_dep(*d) for d in deplist]

    def renew_graph(self,actor=None,attr=None):
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

    def make_actorgraphs(self):
        self.data.make_actorgraphs()
        for act,sub in self.data.actorgraph.iteritems():
            #self.canvas.set_layer(sub,1 )
            self.canvas.add_subgraph(sub,pos=1)

    def del_actorgraphs(self,actor=None):
        if not actor:
            for act in self.actors:
                self.del_actorgraphs(act)
            return
        tokill=[]
        aid=actor.trueID
        tokill.append(self.data.actorgraph[aid])
        del self.data.actorgraph[aid]
        if hasattr(self.data,'actorsubgraphs'):
            for act,dic in self.data.actorsubgraphs.iteritems():
                if aid in dic:
                    tokill.append(dic[aid])
                    del dic[aid]
                if act == aid :
                    for i,j in tuple(dic.iteritems()):
                        tokill.append(j)
                        del dic[i]
            try:
                del self.data.actorsubgraphs[aid]
            except :
                pass
        for i in tokill:
            i.kill()
            self.canvas.rem_subgraph(i)



    def txt_import(self,filename,**kwargs):
        data=MatchData(MatchGraph(),LocCastData(),SettingData())
        data.txt_import(filename)
        self.set_data(data)

    def save_to_file(self,filename):
        self.canvas.graph.pos.update( {i:self.canvas.pos[i]
            for i in self.canvas.pos if i.type in self.canvas.graph.infotypes})
        Handler.save_to_file(self,filename)

    def set_data(self,data):
        self.data=data
        self.canvas.set_graph(data.graph)
        self.cast.clear()
        self.cast.set_data(data.cast)
        self.setting.set_data(data.setting)
        self.ruleset.match=data
        self.make_dependencies()

    def renew(self,**kwargs):
        if 'graph' in kwargs:
            self.canvas.new_graph(kwargs['graph'])
        else:
            self.canvas.new_graph()
        self.cast.clear()
        self.data.renew()

        (c.signal('kill_dependencies') for c in self.components)
        self.signal('kill_dependencies')
        self.make_dependencies()


class MatchEditor(MatchHandler,SceneEditor):
    handlername='Editor'

    def react(self,evt):
        MatchHandler.react(self,evt)
        source=evt.source
        if self.name==source:
            return False
        sgn=evt.type
        sarg=evt.args
        #if 'set_graph' in sgn :
            #self.cast.upd_actors()

        if (hasattr(evt,'item') and isinstance(evt.item,Actor)) or (source and 'cast' in source) :
            if 'add' in sgn:
                self.make_actorgraphs()
            if 'delete' in sgn :
                #todo: complete this
                self.del_actorgraphs(sarg[0])
            if 'unselect' in sgn  :
                self.canvas.set_layer(self.canvas.graph)
                try:
                    user.ui.window['nodelist'].refresh()
                except:
                    pass
            elif 'select' in sgn :
                self.canvas.set_layer(self.data.actorgraph[sarg[0]])
                try:
                    user.ui.window['nodelist'].refresh()
                except:
                    pass

            if ('change' in sgn or 'rem_info' in sgn) and 'name' in evt.kwargs:
                actor=evt.item
                self.data.actorgraph[actor].name=self.cast.get_info(actor,'name')

        if 'flow' in sgn:
            if 'add' in sgn:
                self.make_flow_script(*sarg)
            if 'change' in sgn:
                self.upd_flow_scripts(*sarg)

    def menu(self,event):
        #lam=lambda: self.parent.load_menu('cast',self.cast.add_actor_from_file,new=self.cast.new_actor)
        struct=(('Edit match',lambda e=self.data: self.signal('edit',e)),
            ('Edit setting',lambda e=self.setting.data: self.signal('edit',e)),)
        struct+=SceneEditor.menu(self,event)
        for l in (self.cast,self.canvas.handler,self.setting)  :
            struct+=tuple(l.menu(event))
        act=self.canvas.active_graph
        if act in self.data.actorgraph.values():
            struct+=('Renew subgraph',lambda e=act: self.renew_graph(act.owner)),

        return struct

    def make_flow_script(self,*args):
        link=args[0]
        item=link.parents[0]
        data=args[1]
        if hasattr(data,'owner') and data.owner in [i.trueID for i in self.actors]:
            owner=data.owner
        else:
            owner=None
        genre=self.canvas.get_info(link,'genre')
        s=Script(name=genre)
        print 'MK flowscript',s.name
        cond=MatchScriptCondition()
        effect=MatchScriptEffect()
        s.conds.append(cond)
        s.effects.append(effect)
        dftmodes=link.dft_modes(owner)
        if genre in dftmodes:
            for k,l in dftmodes[genre][0].iteritems():
                cond.set_attr(k,l)
            for k,l in dftmodes[genre][1].iteritems():
                effect.set_attr(k,l)
        evt=ChangeInfosEvt(item,data,scripts=[s],additive=True)
        user.evt.do(evt,self,1,ephemeral=True)
        print 'Mk flowscript conds:',[c.conds for c in data.get_info(item,'scripts')]
        print 'Mk flowscript effects:',[c.effects for c in data.get_info(item,'scripts')]

    def upd_flow_script(self,*args):
        link=args[0]
        item=link.parents[0]
        data=args[1]
        script=self.canvas.flowscript[link]
        print 'TODO: Update flow script!'

    def make_quote(self,item):
        info=self.get_info(item)
        if info['desc']:
            name=info['desc']
        else:
            name=info['name']
        name=self.parent.handler.textmaker.quotify(name)
        #quote=ConvNodeScript(truth='+',cond='Alone')
        quote=ConvNodeScript(truth='all',cond='Default',text=name)
        quote.name='Quote'
        self.change_infos(item,scripts=[quote],update=True)
