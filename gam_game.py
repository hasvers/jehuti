# -*- coding: utf-8 -*-
from gam_import import *
from gam_match_player import *
from gam_cutscene import *
from gam_actscene import *
from gam_cast_chara import *



class GameNode(Node):
    klass_name='GameSceneGraph.Node'
    genres=('match','cutscene','actscene','character','place')
    dft={'name':'scene',
        'genre':'cutscene',
        'desc':'',
        'data':None, #static data
        'state':None, #dynamic data (evolving during play)
        'val':1.
        }


class GameNodeIcon(NodeIcon):
    def make_surface(self,size,mod,infosource,*args,**kwargs):
        color_ext=graphic_chart['icon_node_fill_colors']
        val=infosource.get_info(self.node,'genre')
        if val=='match' :
            color = color_ext[0]
        elif val=='cutscene':
            color=color_ext[1]
        elif val=='actscene':
            color=get_color('y')
        elif val=='character':
            color=get_color('g')
        elif val=='place':
            color=get_color('b')

        #return self.make_circle(size,(array(color_ext[1])-color_ext[0])*val + color_ext[0],mod)
        return self.make_circle(size,color,mod)


class GameLink(Link):
    klass_name='GameSceneGraph.Link'
    dft={'name':'call',
        'genre':'call',
        'genres':('call',),
        'desc':'',
        'val':.5
        }
    genretable={
        ('character','character'):('relation',),
        ('character','place'):('status',),
        ('place','place'):('go',)
         }
    for j in ('match','cutscene','actscene'):
        for i in ('character','place'):
            genretable[ (i,j) ]=('in',)
        for i in ('match','cutscene','actscene'):
            genretable[ (i,j) ]=('call',)

    def __repr__(self):
        return '{}: {}'.format(self.name,[i.name for i in self.parents] )



class GameSubgraph(Subgraph):
    klass_name='GameSceneGraph.Subgraph'

class GameSceneGraph(Graph):
    Node=GameNode
    Link=GameLink
    Subgraph=GameSubgraph
    datatype='scenegraph'

    infotypes={
        'node':('name','genre','desc','val','data'),
        'link':('name','genre','genres','desc','val'),
        }
    def __init__(self,**kwargs):
        Graph.__init__(self,**kwargs)
        self.name='scenegraph'
        self.data_to_node={}

    def remove(self,item):
        if item.type=='node':
            if item.data and item.data in self.data_to_node:
                del self.data_to_node[item.data]
        return Graph.remove(self,item)

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['data_to_node']
        return Graph.txt_export(self,keydic,txtdic,typdic,**kwargs)


class GameData(Data):
    dft={'name':'game','first':None}
    datatype='game'

    infotypes={
        'variable':('val',)
        }

    def __init__(self,**kwargs):
        self.name='game'
        self.first=None
        Data.__init__(self,**kwargs)
        self.graphs=[GameSceneGraph()]
        self.vargraph=nx.DiGraph()

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['graphs','first']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)


    def klassmake(self,klass,*args):
        return eval(klass)(*args)

    def links(self,node):
        for g in self.graphs:
            if node in g.data_to_node:
                n=g.data_to_node[node]
            elif isinstance(node,basestring):
                print node, 'not in game links'
                continue
            else:
                n=node
            if g.contains(n):
                return g.links[n]
        return []

    def get_node(self,node):
        for g in self.graphs:
            if node in g.data_to_node:
                n=g.data_to_node[node]
                return n


class GameState(Data):
    dft={'name':'gamestate','current':None,'node_state':{} }
    datatype='gamestate'

    infotypes={
        'variable':('val',),
        }

    def __init__(self,**kwargs):
        self.name='gamestate'
        self.current=kwargs.get('current',None) #current scene
        Data.__init__(self,**kwargs)
        self.vargraph=nx.DiGraph() #evolving variable graph
        #TODO: how to export vargraph?
        self.node_state={}

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['node_state','current']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def klassmake(self,klass,*args):
        return eval(klass)(*args)


class GameCanvas(Canvas):
    Graph=GameData
    NodeIcon=GameNodeIcon
    LinkIcon=LinkIcon


    def react(self,evt):
        handled=0
        if 'change' in evt.type and evt.item.type=='node':
            if 'data' in evt.infos or 'genre' in evt.infos:
                item=evt.item
                old=evt.oldinfo.get('data')
                if old in self.graph.data_to_node:
                    del self.graph.data_to_node[old]
                if item.data in self.graph.data_to_node:
                    if not self.graph.data_to_node[item.data] in self.graph.nodes:
                        print 'Reinitializing link'
                        self.graph.data_to_node[item.data]=item
                    elif self.graph.data_to_node[item.data] !=item:
                        print 'Already linked',item.data, self.graph.data_to_node[item.data],'(trying to link to {})'.format(item)
                else:
                    self.graph.data_to_node[item.data]=item
        return handled or Canvas.react(self,evt)


class GameHandler(Handler):
    def __init__(self,parent=None,*args,**kwargs):
        Handler.__init__(self,parent=None,**kwargs)
        self.loaded={}
        self.context={}


    def dataload(self,node):
        genre=node.genre
        fname='{}{}'.format(database[genre+'_path'],node.data)
        fin=fopen(fname,'rb')
        return pickle.load(fin)

    def open_node(self,item):
        if isinstance(item,basestring):
            dataname=item
            node = self.data.get_node(dataname)
        else:
            node=item
            dataname=item.data
        if not dataname in self.loaded:
            self.loaded[dataname]=self.dataload(node)
        nei=self.data.links(node)
        for l in nei:
            for n2 in l.parents:
                if not n2 in self.loaded:
                    self.loaded[n2.data]=self.dataload(n2)
        self.context[dataname]=nei


class GameEditor(CanvasEditor,GameHandler):

    data=GameData

    def __init__(self,parent=None,**kwargs):
        GameHandler.__init__(self)
        data=kwargs.get('data',GameData())
        self.data=GameData
        if isinstance(data,basestring):
            self.set_from_file(data,initial=True)
        else:
            self.data=data
        CanvasEditor.__init__(self,GameCanvas(graph=self.data.graphs[0]),parent)
        self.canvas.set_handler(self)

    def label(self,item):
        try:
            return item.label
        except:
            pass
        if hasattr(item,"item"): #if we receive an icon
            item=item.item
        return item.name#self.data.get_info(item)

    def bind_data(self,item):
        genre=item.genre
        fname='{}{}{}'.format(database[genre+'_path'],item.name,database[genre+'_ext'])
        try:
            fin=open(fname,'rb')
            data=pickle.load(fin)
            fin.close()
            print 'Bound loaded:', fname
        except:
            if genre=='match':
                data=MatchData(MatchGraph(),LocCastData(),SettingData(),name=item.name)
            elif genre=='cutscene':
                data=CutsceneData(LocCastData(),SettingData(),name=item.name)
            elif genre=='place':
                data=PlaceData(LocCastData(),name=item.name)
            elif genre=='actscene':
                data=ActsceneData(LocCastData(),SettingData(),name=item.name)
            elif genre=='character':
                data=CharacterData(Actor(name=item.name),MatchGraph(),name=item.name)
                data.truename=data.actor.truename=data.actor.name+str(id(data.actor))
            try:
                data.txt_import(item.name)
            except:
                data.name=item.name
                fout=fopen(fname,'wb')
                pickle.dump(data,fout)
                fout.close()
                print 'Created', fname,data
        data=data.name+database[genre+'_ext']

        item.data=data
        #data.parent=self.data        ##This is not a good idea because parent data
                    ##is useful for imports, so should be more or less same type
        self.canvas.graph.data_to_node[item.data]=item

    def unbind_data(self,item):
        ##TODO:OBSOLETE
        try:
            del self.canvas.graph.data_to_node[item.data]
        except:
            pass
        item.data=None

    def save_to_file(self,filename):
        self.canvas.graph.pos.update( {i:self.canvas.pos[i]
            for i in self.canvas.pos if i.type in self.canvas.graph.infotypes})
        Handler.save_to_file(self,filename)
        try:
            os.mkdir(database['game_path']+ filename)
        except:
            pass

    def set_first(self,item):
        evt=ChangeInfosEvt(self.data,None,first=item,itemwrite=True)
        return user.evt.do(evt,self,None,ephemeral=False)

    def bgmenu(self,main=True):
        if main :
            bgmenu = [ ('Edit game', lambda e=self.data: self.signal('edit',e)),
            ('Add node',lambda p=self.mousepos():self.add_node(None,None,pos=p)),
                #('Add subgraph',self.add_subgraph),
                ]
        else :
            bgmenu = [

                ]
        if not user.ui.view['nodelist']:
                bgmenu += [('Node list',lambda:user.ui.show('nodelist') )]
        return bgmenu

    def maingraph_menu(self,target,typ,event=None):
        struct=()
        if not ergonomy['edit_on_select']:
            struct+=( ('Edit',lambda t=target: self.signal('edit',t)), )

        if typ == 'node':
            struct += ('Add link',lambda t=target: self.start_linkgrabber(t)),
            try:
                handled=self.dataload(target.item)
            except:
                handled=None
            if handled:
                struct+=('Open',lambda t=target.item: self.signal('open',t)),
                struct+=('Unbind data', lambda t=target.item: self.unbind_data(t)),
            else:
                struct+=('Bind data', lambda t=target.item: self.bind_data(t)),
            struct+=('Delete node',lambda t=target: self.rem_node(t.node)),
            struct+=('Set first scene',lambda t=target: self.set_first(t.node)),
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

    def replace_variables(self,txt):
        if '\[' in txt:
            for g in self.data.variables:
                txt=txt.replace('\[{}]'.format(g.name),str(self.data.get_info(g,'val')) )
        return txt


    def set_data(self,data):
        Handler.set_data(self,data)
        self.canvas.set_graph(data.graphs[0])


    def end_linkgrabber(self,grabber,event):
        user.ungrab()
        newevent=pgevent.Event( pg.MOUSEMOTION,pos=self.mousepos(),rel=(0,0))
        self.event(newevent)
        if isinstance(self.hovering,self.canvas.NodeIcon):
            for i in grabber.ilinks :
                newp=[self.hovering.node if p==grabber else p for p in i.link.parents]
                genres=tuple(self.canvas.get_info(p,'genre') for p in newp)
                if newp[0]!=newp[1] and genres in i.link.genretable :
                    lgen=i.link.genretable[genres]
                    infos= self.canvas.get_info(i.link)
                    infos.update({'genre':lgen[0],'genres': tuple(lgen), 'name':lgen[0]})
                    self.canvas.remove(i.link)
                    evt = AddEvt(self.canvas.active_graph.Link(tuple(newp)),self.canvas.active_graph,infos=infos )
                    user.evt.do(evt,self)
                else :
                    self.canvas.remove(i.link)
        else :
            for i in grabber.ilinks:
                self.canvas.remove(i.link)
        grabber.kill()
        return True

class GamePlayer(GameHandler):
    #general access to ongoing game state and general functions
    def __init__(self,*args,**kwargs):
        GameHandler.__init__(self,*args,**kwargs)
        self.gamestate= kwargs.get('gamestate',None)
        if self.gamestate is None:
            self.gamestate=GameState()
            for g in self.data.variables:
                self.gamestate.add(g)

    def set_variable(self,varname,value,**kwargs):
        #Add vartree effects
        variable=[v for v in self.gamestate.variables if v.name==varname] [0]
        if not self.gamestate:
            print 'No gamestate'
            return
        if isinstance(value,basestring):
            value=self.replace_variables(value)

        if kwargs.get('batch',None):
            evt= ChangeInfosEvt(variable,self.gamestate,val=value )
            batch.add_event(evt)
            evt.parent=batch
            batch.add_child(evt,{1:0,2:1},priority=1)
        else:
            self.gamestate.set_info(variable,'val',value)


    def replace_variables(self,txt):
        if '\[' in txt:
            for g in self.gamestate.variables:
                txt=txt.replace('\[{}]'.format(g.name),str(self.gamestate.get_info(g,'val')) )
        return txt

    def menu(self,event):
        struct=()
        #struct+=('Exit',lambda:user.ui.return_to_title ),
        return struct

    def keymap(self,event):
        handled=False
        if event.key==pg.K_ESCAPE :
            if not user.paused:
                struct=()
                try:
                    if user.ui.scene.stack:
                        call=None
                        for j in user.ui.scene.stack:
                            if 'call' in j.type:
                                call=j
                                break
                        if call:
                            struct+=('Skip',user.ui.scene.skip_to(call)),
                except:
                    pass
                sm=self.save_state
                path=database['game_path']+self.data.name.split('.')[0]+'/'
                struct+=('Save', lambda s=sm,p=path:user.ui.save_menu('save',s,path=p,
                    default=self.gamestate.name,exit_method=lambda:user.pause(False))),

                struct+=('Exit',lambda: user.ui.confirm_menu(lambda:user.ui.game_ui.goto('title'),
                    pos='center',legend='Exit to title screen?') ),
                user.pause(True)
                user.ui.float_menu(struct,pos='center')
            else:
                user.pause(False)
                user.ui.close('floatmenu')
            handled=1
        return handled

    def save_state(self,name=None,**kwargs ):
        if name:
            self.gamestate.name=name
        if kwargs.get('current',0):
            self.gamestate.current=kwargs['current']
        fname='{}{}/{}{}'.format(database['game_path'],self.data.name,self.gamestate.name,database['save_ext'])
        print 'Saving state', fname
        fout=fopen(fname,'wb')
        pickle.dump(self.gamestate,fout)
        return


    def goto(self,node,memory=1):
        if not memory:
            try:
                del self.gamestate.node_state[self.gamestate.current]
            except:
                pass
        self.gamestate.current=node.data
        if not node.data in self.gamestate.node_state:
            state=user.ui.scene.data
            self.gamestate.node_state[node.data]=state
        #if isinstance(node,basestring):
            #node=self.data.is_data_to_node(node)
        #genre,data=node.genre,self.dataload(node)
        #if genre=='match':
            #ui=MatchUI
        #elif genre=='cutscene':
            #ui=CutsceneUI
        #
        #user.set_ui(ui(user.ui.screen,data,game=self),False)

    def end_game(self):
        self.save_state('~'+self.data.name+'.END')
        self.gamestate=GameState()


class GameNodePanel(NodePanel):
    attrs=(('name','input','Name',80,{'charlimit':20}),
            ('genre','listsel','Genre',120,{'values':GameSceneGraph.Node.genres}),
            ('data','listsel','Data',120,{'values':(None,) }),
            ('val','drag', 'Magnitude',80,{'minval':.5,'maxval':2.}),
            ('desc','input','Description',190,{'height':140,'wrap':True}),)

    def make_attrs(self,**kwargs):
        if not self.ref:
            return
        genre=self.ref.genre
        cand = filter(lambda e: database['{}_ext'.format(genre)]
            in e,olistdir(database['{}_path'.format(genre)]))
        if cand == self.attrs[1][4]['values']:
            return False
        data=self.ref.data
        if not data in cand:
            data=''
            #self.ref.data=data
            #self.ref.data=self.dataload(cand[0])
            #self.send_info('data',cand[0],False)
        oldattrs=self.attrs[:]
        self.attrs=(
            ('name','input','Name',80,{'charlimit':20}),
            ('genre','listsel','Genre',120,{'val':genre,'values':GameSceneGraph.Node.genres,'remake':True}),
            ('data','listsel','Data',120,{'val':data,'values':['']+cand}),#,'typecast':lambda e:e}),
            ('val','drag', 'Magnitude',80,{'minval':.5,'maxval':2.}),
            ('desc','input','Description',190,{'height':140,'wrap':True}),
        )
        if not kwargs.get('differential',False):
            self.make()
            return True
        difference= len(self.attrs) != len(oldattrs)
        optdif={}
        i=0
        while not difference  and i < len(oldattrs):
            old,new=oldattrs[i],self.attrs[i]
            if old[:4]!=new[:4]:
                difference=1
            if old[4]!=new[4]:
                optdif[new[0]]=new[4]
            i+=1
        if difference:
            self.make()
        elif optdif:
            print 'TODO:', optdif
        return True

    def __init__(self,*args,**kwargs):
        self.make_attrs()
        NodePanel.__init__(self,*args,**kwargs)

    def set_ref(self,ref,*args,**kwargs):
        #self.genre=self.data.get_info(ref,'genre')
        self.ref=ref
        self.make_attrs()
        NodePanel.set_ref(self,ref,**kwargs)


class GameLinkPanel(LinkPanel):
    def __init__(self,*args,**kwargs):
        self.make_attrs()
        LinkPanel.__init__(self,*args,**kwargs)

    def set_ref(self,ref,*args,**kwargs):
        self.ref=ref
        self.make_attrs()
        LinkPanel.set_ref(self,ref,**kwargs)

    def make_attrs(self,*args,**kwargs):
        if self.ref:
            genres=self.infosource.get_info(self.ref,'genres')
        else:
            genres=('None',)
        self.attrs=(('name','input','Name',80,{'charlimit':20}),
            ('genre','arrowsel','Genre',120,{'values':genres}),
            ('val','drag', 'Magnitude',80,{'minval':.0,'maxval':1.}),
            ('desc','input','Description',190,{'height':140,'wrap':True}),)


class GamePanel(SidePanel):
    title = 'Game editor'
    attrs=(
        ('name','input','Title',100,{'charlimit':20}),
        ('variables','inputlist','Variables',200,{'add':True,'menu':{'type':'variable'}}),
        )