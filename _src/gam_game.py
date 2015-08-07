# -*- coding: utf-8 -*-
from gam_import import *
from gam_match_player import *
from gam_cutscene import *
from gam_actscene import *
from gam_cast_chara import *

#from gam_world import DataWorld

class GameNode(Node):
    klass_name='GameSceneGraph.Node'
    genres=('match','cutscene','actscene','character','place','topic')
    dft={'name':'scene',
        'genre':'cutscene',
        'desc':'',
        'filename':None, #static data - filename
        'dataID':None, #static data - ID
        'state':None, #dynamic data (evolving during play) - ID
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
        elif val=='topic':
            color=get_color('r')

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
        ('place','place'):('go',),
        ('topic','character'):('in',)
         }
    for j in ('match','cutscene','actscene'):
        for i in ('character','place','topic'):
            genretable[ (i,j) ]=('in',)
        for i in ('match','cutscene','actscene'):
            genretable[ (i,j) ]=('call',)

    def __str__(self):
        return '{}: {}'.format(self.name,[i.name for i in self.parents] )



class GameSubgraph(Subgraph):
    klass_name='GameSceneGraph.Subgraph'
    '''Subgraph of GameSceneGraph, allows for instance to look only
    at a certain type of scenes and objects.'''


class GameSceneGraph(Graph):
    '''Graph of the relations between scenes and objects in the game.
    '''
    Node=GameNode
    Link=GameLink
    Subgraph=GameSubgraph
    datatype='scenegraph'
    overwrite_item=True


    infotypes={
        'node':('name','genre','desc','val','filename','dataID'),
        'link':('name','genre','genres','desc','val'),
        }
    def __init__(self,**kwargs):
        Graph.__init__(self,**kwargs)
        self.name='scenegraph'
        self.refresh_dict()

    def refresh_dict(self):
        self.data_to_node={}
        for n in self.nodes:
            if n.dataID and n.dataID in self.data_to_node:
                print 'ERROR: The same data is already attached to another node',n.dataID,self.data_to_node[n.dataID],n
                continue
            self.data_to_node[n.dataID]=n

    def remove(self,item):
        if item.type=='node':
            del self.data_to_node[item.dataID]
        return Graph.remove(self,item)

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        return Graph.txt_export(self,keydic,txtdic,typdic,**kwargs)


class GameData(Data):
    '''Main data structure for a whole game. Does not contain the data of
    any given scene, only gamewide variables and a graph whose nodes contain
    the identifier and filename for each scene.
    '''

    dft={'name':'game','first':None}
    datatype='game'

    infotypes={
        'variable':('val',)
        }

    def __init__(self,**kwargs):
        self.name='game'
        self.first=None
        Data.__init__(self,**kwargs)
        self.graph=GameSceneGraph()
        self.graph.game=self
        #self.graphs=[]

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['graph','first']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def links(self,node_or_data):
        g=self.graph
        if node_or_data in g.data_to_node:
            n=g.data_to_node[node_or_data]
        elif isinstance(node_or_data,basestring):
            print 'ERROR:', node_or_data, 'not in game links'
            return []
        else:
            n=node_or_data
        if g.contains(n):
            return [(l,l.other_parent(n)) for l in g.links[n]]
        return []

    def get_node(self,data):
        if hasattr(data,'dataID'):
            data=data.dataID
        return self.graph.data_to_node[data]


class GameState(Data):
    '''Changing state for a GameData structure.
    Contains a dictionary of current node states for all the evolving nodes
    Contains a graph of variables that remembers which event in which scene
    changed which variable throughout the playtime, for easier debugging.'''

    dft={'name':'gamestate','current':None,'node_state':{} }
    datatype='gamestate'

    infotypes={
        'variable':('val',),
        }

    def __init__(self,**kwargs):
        self.name='gamestate'
        self.current=kwargs.get('current',None) #current scene
        Data.__init__(self,**kwargs)
        self.node_state=DataDict()

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['node_state','current']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

class GameCanvas(Canvas):
    Graph=GameData
    NodeIcon=GameNodeIcon
    LinkIcon=LinkIcon


    def react(self,evt):
        handled=0
        if ('change' in evt.type or 'rem_info' in evt.type)  and evt.item.type=='node':
            if not 'dataID' in evt.infos and 'genre' in evt.infos:
                #If I change the genre of a node, I should set its attached dataID to None
                evt.oldinfo['dataID']=self.get_info(evt.item,'dataID')
                evt.kwargs['dataID']=None
                evt.item.dataID=None
            if 'filename' in evt.infos:
                #If I change the data, I have to change data_to_node
                #First remove association with previous dataname
                self.graph.refresh_dict()
                self.handler.dataload(evt.item)
        if 'add' in evt.type  and evt.item.type=='node':
                self.handler.dataload(evt.item)
        return handled or Canvas.react(self,evt)


class GameHandler(Handler):
    def __init__(self,parent=None,*args,**kwargs):
        Handler.__init__(self,parent=None,**kwargs)
        self.loaded={}

    def set_data(self,data):
        self.loaded={}
        self.data=data
        for n in self.data.graph.nodes:
            self.dataload(n)
        self.renew()

    def dataload(self,node):
        genre=node.genre
        if not node.filename:
            return None
        if not node.filename in self.loaded:
            for l, nei in self.data.links(node):
                if l.genre=='in' and node==l.parents[1]:
                    self.dataload(nei)
            print 'loading',node.filename
            try:
                fin=fopen(node.filename,'rb',filetype=genre)
                fin.close()
            except Exception as e:
                print "Couldn't load {}".format(node.filename),e
                return None
            items=world.explore_file(resource_path(node.filename,filetype=genre))
            if not node.dataID:
                node.dataID=[i for i in items if eval(world.future_data[i]['klass'])==self.klass_data(genre) ][0]

            data=world.make_data(node.dataID)
            #data=self.blank_data(node.name,genre)
            #data.txt_import(node.filename)
            self.loaded[node.filename]=data
            self.data.graph.set_info(node,'dataID',data.trueID)
            self.data.graph.refresh_dict()
        else:
            data=self.loaded[node.filename]
        return data

    def datarem(self,node):
        if node.filename in self.loaded:
            del self.loaded[node.filename]
        self.data.graph.set_info(node,'dataID',None)

    def blank_data(self,name,genre):
        if genre=='match':
            data=MatchData(MatchGraph(),LocCastData(),SettingData(),name=name)
        elif genre=='cutscene':
            data=CutsceneData(LocCastData(),SettingData(),name=name)
        elif genre=='place':
            data=PlaceData(LocCastData(),name=name)
        elif genre=='actscene':
            data=ActsceneData(LocCastData(),SettingData(),name=name)
        elif genre=='character':
            data=CharacterData(Actor(name=name),MatchGraph(),name=name)
        elif genre=='topic':
            data=MatchGraph(name=name)
        data.name=name
        return data

    def klass_data(self,genre):
        if genre=='match':
            return MatchData
        elif genre=='cutscene':
            return CutsceneData
        elif genre=='place':
            return PlaceData
        elif genre=='actscene':
            return ActsceneData
        elif genre=='character':
            return CharacterData
        elif genre=='topic':
            return MatchGraph

    def create_data(self,node):
        '''Create data for a scene/object that bears the name of the node'''
        name=node.name
        data=self.blank_data(name,node.genre)
        #fout=fopen(name,'wb',filetype=node.genre)
        #pickle.dump(data,fout)
        node.dataID=data.trueID
        node.filename=name
        data.txt_export(filename=name )
        #fout.close()
        self.data.graph.set_info(node,'filename',node.name)
        self.dataload(node)

    def delete_data(self,node):
        '''Delete data bound to a node'''
        fremove(node.filename,filetype=node.genre)
        self.datarem(node)

    def get_sources_for(self,caller,typ):
        '''Find all possible sources of importable entities in the
        neighborhood of a caller (some scene, identified by its data)'''
        src=[]
        #print caller,typ
        #node=None
        #for n,s in self.loaded.iteritems():
            #if s == caller:
                #node=n
                #break
            #elif str(s)==str(caller):
                #print 'ERROR: Get sources --', s,caller, id(s),id(caller)
        #if not node:
            #return src
        for l,nei in self.data.links(caller.trueID):
            if nei.genre==typ:
                src.append(world.database[nei.dataID])
        return src



class GameEditor(CanvasEditor,GameHandler):

    data=GameData

    def __init__(self,parent=None,**kwargs):
        GameHandler.__init__(self)
        data=kwargs.get('data',GameData())
        if isinstance(data,basestring):
            self.set_from_file(data,initial=True,klass='GameData',datatype='game')
        else:
            self.data=data
        CanvasEditor.__init__(self,GameCanvas(graph=self.data.graph),parent)
        self.canvas.set_handler(self)

    def label(self,item):
        try:
            return item.label
        except:
            pass
        if hasattr(item,"item"): #if we receive an icon
            item=item.item
        return item.name#self.data.get_info(item)


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
                bgmenu += [('Show node list',lambda:user.ui.show('nodelist') )]
        return bgmenu

    def maingraph_menu(self,target,typ,event=None):
        struct=()

        if typ == 'node':
            node=target.item
            dataname =node.filename
            #print dataname, node.dataID, world.database
            try:
                existing=fopen(dataname,'rb',filetype=node.genre)
                #print dataname, existing
            except:
                existing=False
            if node.dataID in world.database or existing:
                struct+=('Open data',lambda t=node: self.signal('open',t)),
                existing=True
            if existing:
                dmeth=lambda t=node: self.delete_data(t)
                struct+=('Delete data',lambda:self.parent.confirm_menu(dmeth,
                        legend="Delete data? (IRREVERSIBLE)") ),
            else:
                struct+=('Create data',lambda t=node: self.create_data(t)),
            if not ergonomy['edit_on_select']:
                struct+=( ('Edit node',lambda t=target: self.signal('edit',t)), )

            struct += ('Add link',lambda t=target: self.start_linkgrabber(t)),
            struct+=('Delete node',lambda t=target: self.rem_node(t.node)),
            struct+=('Set first scene',lambda t=target: self.set_first(t.node)),
            return struct
        if typ == 'link' :
            if not ergonomy['edit_on_select']:
                struct+=( ('Edit link',lambda t=target: self.signal('edit',t)), )
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

    def set_data(self,data):
        GameHandler.set_data(self,data)
        self.canvas.set_graph(data.graph)


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
        self.data=GameData()
        data=kwargs.get('data',self.data)
        if isinstance(data,basestring):
            self.set_from_file(data,initial=True,klass='GameData',datatype='game')
        else:
            self.data=data

        state= kwargs.get('gamestate',None)
        if isinstance(state,basestring):
            path='{}{}/'.format(database['game_path'],gamedata.name)
            if not path in state:
                path='{}{}{}'.format(path,state,database['save_ext'])
            self.gamestate=self.get_from_file(data,initial=True,klass='GameState')
        elif state is None:
            self.gamestate=GameState()
            for g in self.data.variables:
                self.gamestate.add(g)
        else:
            self.gamestate=state

    def set_variable(self,varname,value,**kwargs):
        variable=[v for v in self.gamestate.variables if v.name==varname] [0]
        if not self.gamestate:
            print 'No gamestate'
            return
        if isinstance(value,basestring):
            try:
                #If the value is given as a text that involves some entities
                #in the world
                nval=eval(value,globals,self.world.name)
            except:
                nval=value
            value=nval

        if kwargs.get('batch',None):
            evt= ChangeInfosEvt(variable,self.gamestate,val=value )
            batch.add_event(evt)
            evt.parent=batch
            batch.add_child(evt,{1:0,2:1},priority=1)
        else:
            self.gamestate.set_info(variable,'val',value)

    def menu(self,event):
        struct=()
        #struct+=('Exit',lambda:user.ui.return_to_title ),
        return struct

    def keymap(self,event):
        handled=False
        if event.key==pg.K_ESCAPE :
            if not user.paused:
                struct=()
                scr =user.ui.scene.get_scripts(call='skip')
                if scr:
                    struct+=('Skip',user.ui.scene.skip_to(scr[0] )),
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
        #fout=fopen(fname,'wb')
        #pickle.dump(self.gamestate,fout)
        self.gamestate.txt_export(filename=fname)
        return


    def goto(self,node,memory=1):
        if not memory:
            try:
                del self.gamestate.node_state[self.gamestate.current]
            except:
                pass
        self.gamestate.current=node.dataID
        if not node.dataID in self.gamestate.node_state:
            state=user.ui.scene.data
            self.gamestate.node_state[node]=state
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
            ('filename','listsel','Data',120,{'values':(None,) }),
            ('val','drag', 'Magnitude',80,{'minval':.5,'maxval':2.}),
            ('desc','input','Description',190,{'height':140,'wrap':True}),)

    def make_attrs(self,**kwargs):
        if not self.ref:
            return
        genre=self.ref.genre
        cand = filter(lambda e: database['{}_ext'.format(genre)]
            in e,olistdir(database['{}_path'.format(genre)]))
        cand =[c.replace( database['{}_ext'.format(genre)],'') for c in cand ]
        if cand == self.attrs[1][4]['values']:
            return False
        data=self.ref.filename
        if not data in cand:
            data=''
            #self.ref.data=data
            #self.ref.data=self.dataload(cand[0])
            #self.send_info('data',cand[0],False)
        oldattrs=self.attrs[:]
        self.attrs=(
            ('name','input','Name',80,{'charlimit':20}),
            ('genre','listsel','Genre',120,{'val':genre,'values':GameSceneGraph.Node.genres,'remake':True}),
            ('filename','listsel','Data',120,{'val':data,'values':['']+cand}),#,'typecast':lambda e:e}),
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