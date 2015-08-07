from gam_match_gui import *
from gam_game import *

class MenuUI(BasicUI):
    def __init__(self,screen,**kwargs):
        temp=ergonomy
        BasicUI.__init__(self,screen,template=temp,**kwargs)

class StartMenuUI(MenuUI):
    def __init__(self,screen,**kwargs):
        temp={'viewables':('floatmenu','menu') ,'menu':True,'floatmenu':True}
        BasicUI.__init__(self,screen,template=temp,**kwargs)
        self.bg=pg.transform.smoothscale(image_load(database['image_path']+database['title_bg']),self.rect.size).convert()


        gcand = filter(lambda e: database['game_ext'] in e and not '~' in e,olistdir(database['game_path']))
        savcand={}
        for g in gcand:
            savcand[g] = filter(lambda e: database['save_ext'] in e,olistdir(database['game_path']+g.split('.')[0]))

        #mcand = filter(lambda e: database['match_ext'] in e,olistdir(database['match_path']))
        gedit=GameEditorUI
        gui=GameUI
        #medit=MatchEditorUI
        ginit=GameData

        if savcand:
            def savloadscreen(game,cand):
                savcand=cand[game]
                if len(savcand)>1:
                    path=database['game_path']+game.split('.')[0]+'/'
                    smenu=lambda s,game=game,u=user: u.set_ui( gui(screen,game,gamestate=s))
                    return self.load_menu(savcand,smenu,path=path,new=None)
                elif len(savcand)==1:
                    return u.set_ui( gui(screen,s))

        savmenu=None
        if len(gcand)>1:
            ed=lambda game, u=user: u.set_ui(gedit(screen,game))
            edmenu=lambda e=ed:self.load_menu('game',e,new=lambda:ed(ginit()))
            pl=lambda game,u=user: u.set_ui( gui(screen,game))
            plmenu=lambda e=pl:self.load_menu('game',e,new=None)
            spl=lambda e,c=savcand:savloadscreen(e,c)
            savmenu=lambda e=spl:self.load_menu('game',e,new=None)
        elif len(gcand)==1:
            game=gcand[0].split('/')[-1].replace(database['game_ext'],'')
            edmenu=lambda game=game, u=user: u.set_ui(gedit(screen,game))
            plmenu=lambda game=game,u=user: u.set_ui( gui(screen,game))
            savcand=savcand[gcand[0]]
            if len(savcand)>1:
                path=database['game_path']+g.split('.')[0]+'/'
                smenu=lambda s,game=game,u=user: u.set_ui( gui(screen,game,gamestate=s))
                savmenu=lambda e=smenu,p=path:self.load_menu(savcand,e,path=p,new=None)
            elif len(savcand)==1:
                s=savcand[0].replace(database['save_ext'],'')
                savmenu=lambda  s=s,game=game, u=user: u.set_ui( gui(screen,game,gamestate=s))
        else:
            edmenu=lambda game=ginit, u=user: u.set_ui(gedit(screen,game() ))
            plmenu=None
        #if mcand:
            #medmenu=lambda match=mcand[0].replace(database['match_ext'],''), u=user: u.set_ui(medit(screen,match))

        mopt={'output_method':edmenu,'selectable':True}
        struct=()
        if database['edit_mode']==False:
            mopt['state']='disabled'
        else:
            struct+=(
            ('Edit','text',mopt),)
            #('Edit last match','text',{'output_method':medmenu,'selectable':True}),)
        if plmenu:
            sopt={'output_method':savmenu,'selectable':True}
            if not savmenu:
                sopt.update({'state':'disabled'})
            struct+=(
            ('Play','text',{'output_method':plmenu,'selectable':True}),
            ('Load','text',sopt),
            )
        struct+=('Exit','text',{'output_method':lambda: pgevent.post(pgevent.Event(pg.QUIT)),
            'selectable':True}),
        window=FloatMenu(self.screen,self,(128,10),struct=struct,font=FONTLIB["title"],drag=False)
        window.update()
        window.rect.center=self.screen.get_rect().center

        self.pos[window]=window.rect.topleft
        self.window['menu']=window
        self.group.add(window)

    def launch(self):
        user.music.play(database['title_music'])
        MenuUI.launch(self)
        if not database['edit_mode']:
            w=self.window['menu']
            w.set_anim('appear',ANIM_LEN['med'],interpol='quad')
            for c in w.children:
                c.set_anim('appear',ANIM_LEN['long'],interpol='quad')

    def general_menu(self,event=None):
        return False

    #def launch(self):
        #if database['edit_mode']==False:
            #self.window['menu'].fieldict['Edit'].set_state('disabled')

class GameEditorUI(EditorUI):
    def __init__(self,screen,gamedata,**kwargs):
        self.soundmaster = EditorSM(self)
        self._screen=screen
        self.game =  GameEditor(self,data=gamedata)
        self.children_ui={}
        game =self.game.canvas
        if self.statusmenu():
            smenu=[('Menu',self.statusmenu)]
        else:
            smenu=False
        wintypes=kwargs.pop('wintypes',dict((  ('statusbar',lambda e: StatusBar(e,menu=smenu)),
                        ('nodelist',lambda e,t=game.handler:NodeList(e,t) ),
                        ('sidepanel',lambda e,t=game:SidePanel(e,t)),
                        ('nodepanel',lambda e,t=game: GameNodePanel(e,t)),
                        ('linkpanel',lambda e,t=game: GameLinkPanel(e,t)),
                        ('gamepanel',lambda e,t=game: GamePanel(e,t,itemwrite=True)),
                    )))
        sidetypes=kwargs.pop('sidetypes',('nodepanel','linkpanel','gamepanel'))


        super(GameEditorUI, self).__init__(screen,None,wintypes=wintypes,sidetypes=sidetypes,**kwargs)
        self.layers.append(self.game)

    def kill(self,*args):
        for i,j in self.children_ui.iteritems():
            j.kill(*args)
        EditorUI.kill(self,*args)

    def make_dependencies(self):
        BasicUI.make_dependencies(self)

        self.game.make_dependencies()
        deplist=(
            (self,self.game),
            (self,self.game.data),
        )
        for d in deplist:
            self.depend.add_dep(*d)
        if self.window['statusbar']:
            self.depend.add_dep(self.window['statusbar'],user)

    def launch(self):
        EditorUI.launch(self)
        for n in self.game.data.graph.nodes:
            self.game.dataload(n)
        if ergonomy["editor_memory"]:
            nam=None
            try:
                with fopen('logs/.editor_last','r') as last :
                    for l in last:
                        if l:
                            nam=l
                            break
                if not nam is None:
                    self.open_editor(nam)
                    print 'Loading last map:',world.database[world.get_object(nam).dataID]
            except:
                pass

    @property
    def components(self):
        return (self.game,)

    def input_menu(self,typ,output_method,**kwargs):
        if typ=='variable':
            return self.var_maker(output_method,**kwargs)
        else :
            return super(GameEditorUI, self).input_menu(typ,output_method,**kwargs)

    def var_maker(self,output_method,**kwargs):
        flist=(
            ('name', 'input'), ('val','input'),
            )
        kwargs.setdefault('title','Game variable:')
        self.maker_menu(flist,output_method,GameVariable,**kwargs)

    def statusmenu(self):
        m=self.game
        lams=lambda: self.save_menu('game',m.save_to_file,default=m.data.name)
        lamn=lambda: m.set_data(GameData() )
        laml=lambda: self.load_menu('game',m.set_from_file,new=lamn)
        struct=('Save game',lams),('Load game',laml)
        if m.data.first:
            struct +=('Start game',lambda e=None: m.signal('start_game')),
        lamg=lambda:m.data.txt_export(filename=m.data.name)
        lami=lambda e:m.data.txt_import(filename=e)
        struct+=('Export game as text',lamg),
        struct+=('Import game from text',lambda:self.load_menu('game',lami,ext='.arc.txt') ),
        struct+= ('Exit',self.return_to_title),
        return struct

    def return_to_title(self):
        self.game.save_to_file('archive/last.dat')
        user.set_ui(StartMenuUI(self._screen))


    def keymap(self,event):
        handled=False
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_s :
                g=self.game
                g.save_to_file(g.data.name)
                user.set_status('Saved as '+g.data.name)
                handled=True
        return handled or EditorUI.keymap(self,event)

    def open_editor(self,item):
        '''Given a node, open the editor of the data linked to that node'''
        #If we receive a trueID instead:
        if isinstance(item,basestring):
            item=world.get_object(item)
        data= world.database[item.dataID]
        #Log the trueID of the currently open scene
        with fopen('logs/.editor_last','w') as last :
            last.write(item.trueID)
        if data in self.children_ui:
            user.set_ui(self.children_ui[data])#,no_launch=True)
        else:
            genre=item.genre
            if genre=='match':
                edit=MatchEditorUI
            elif genre=='cutscene':
                edit=CutsceneEditorUI
            elif genre=='actscene':
                edit=ActsceneEditorUI
            elif genre=='place':
                edit=PlaceEditorUI
            elif genre=='character':
                edit=CharacterEditorUI
            elif genre=='topic':
                TopicEditorUI
            newui=edit(self._screen, data,game_ui=self)
            #self.children_ui[data]=newui
            #TODO: children_ui doesn't work yet
            user.set_ui(newui,False)

    def react(self,evt,**kwargs):
        if 'open' in evt.type:
            #self.game.dataload(evt.args[0])
            self.open_editor(evt.args[0])
        if 'start_game' in evt.type :
            return user.set_ui(GameUI(self._screen,self.game.data),False )
            #item=self.editor.data.first
            #genre,data=item.genre,self.dataload(item)
            #if genre=='match':
                #ui=MatchUI
            #elif genre=='cutscene':
                #ui=CutsceneUI
            #return user.set_ui( ui(self._screen,data),False )
        EditorUI.react(self,evt,**kwargs)

class GameUI(BasicUI):
    name='GameUI'
    def __init__(self,screen,gamedata,**kwargs):
        #BasicUI.__init__(self,screen)
        self._screen=screen
        self.depend=DependencyGraph()
        if 0:
            if isinstance(gamedata,basestring):
                path=database['game_path']
                if not path in gamedata:
                    path='{}{}{}'.format(path,gamedata,database['game_ext'])
                else:
                    path=gamedata
                #gfin=fopen(path,'rb')
                gamedata=GameData()
                gamedata.txt_import(path)
                #gamedata=pickle.load(gfin)
            gamestate= kwargs.get('gamestate',None)
            if isinstance(gamestate,basestring):
                path='{}{}/'.format(database['game_path'],gamedata.name)
                if not path in gamestate:
                    path='{}{}{}'.format(path,gamestate,database['save_ext'])
                else:
                    path=gamestate
                gamestate=GameState()
                gamestate.txt_import(path)
                #gfin=fopen(path,'rb')
                #gamestate=pickle.load(gfin)
        self.game= GamePlayer(self,data=gamedata,gamestate=kwargs.pop('gamestate',None) )

    def launch(self):
        if self.game.gamestate.current:
            first= self.game.gamestate.current
        else:
            first=self.game.data.first
        self.goto(first)
        self.launched=True

    def goto(self,node,**kwargs):
        if node=='END':
            self.game.end_game()
            node='title'
        if node=='title':
            user.pause(0)
            return user.set_ui(StartMenuUI(self._screen))
        if isinstance(node,basestring):
            node=self.game.data.get_node(node)
        #current= user.ui
        #if current != self:
            #try:
                #current.match.freeze()
            #except:
                #current.scene.freeze()
        genre=node.genre
        state= self.game.gamestate.node_state.get(node,None)
        if state:
            data=state
        else:
            data=self.game.dataload(node)
        if genre=='match':
            ui=MatchUI
        elif genre=='cutscene':
            ui=CutsceneUI
        elif genre=='place':
            ui=PlaceUI
        elif genre=='actscene':
            ui=ActsceneUI
        newui=ui(user.ui._screen,data,game_ui=self)
        if 'splash' in kwargs and kwargs['splash']:
            tdevt=kwargs['splash']
            tdevt.state=0
            tdevt.step=0
            tdevt.tinit=None
            tdevt.mod=tdevt.mod[::-1]
            tdevt.block_thread=0
            scene=newui.scene
            newui.veils['fade']=self.screen.copy()
            scene.add_phase(tdevt)
        user.set_ui(newui,False)
        self.game.goto(node)
        user.pause(0)

#