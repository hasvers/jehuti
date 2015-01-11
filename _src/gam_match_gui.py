# -*- coding: utf-8 -*-
from gam_import import *
from gam_canvas import *
from gam_match_player import *
import os


class MatchNodePanel(NodePanel):
    attrs=(
        ('name','input','Name',190,{'charlimit':90}),
        ('genre','arrowsel','Genre',120,{'values':MatchGraph.Node.genres}),
        ('val','drag', 'Magnitude',80,{'minval':.5,'maxval':2.}),
        ('subt','drag', 'Subtlety',80,{'minval':0.,'maxval':1.}),
        ('bias','drag','Bias',80,{'minval':-1.,'maxval':1.,'color':graphic_chart['icon_node_fill_colors'][:2]}),
        #('cflags','arrowsel','Inclusion',120,{'values':MatchGraph.Node.cflags}),
        ('desc','input','Description',190,{'height':140,'wrap':True}),
        ('cflags','inputlist','Flags',200,{'add':True,'menu':{'type':'cflags'}}),
        #('quotes','inputlist','Quotes',200,{'add':True,'menu':{'type':'quotes'}}),
        ('scripts','inputlist','Scripts',200,{'add':True,'menu':{'type':'nscript'}}),
        ('effects','inputlist','Ethos',200,{'add':True,'unique':True,'menu':{'type':'ethos'}})

    )


class MatchLinkPanel(LinkPanel):
    attrs=[
#        ('name','input','Name',80,{'charlimit':10}),
        ('pattern','arrowsel','Pattern',120,{'values':MatchGraph.Link.patterns}),
        ('logic','ltyp','Logic',80,{'val':(1,1),'color':graphic_chart['icon_node_fill_colors'][:2]}),
        ('val','drag', 'Magnitude',80,{'minval':0.,'maxval':1.}),
        ('subt','drag', 'Subtlety',80,{'minval':0.,'maxval':1.}),
        ('desc','input','Description',120,{'height':200,'wrap':True}),
        #('quotes','inputlist','Quotes',200,{'add':True,'menu':{'type':'lquotes'}}),
        ('scripts','inputlist','Scripts',200,{'add':True,'menu':{'type':'lscript'}}),
        ('cflags','inputlist','Flags',200,{'add':True,'unique':True,'menu':{'type':'cflags'}}),
    ]

    def make(self):
        SidePanel.make(self,cats={'ltyp':self.input})



class MatchPanel(SidePanel):
    title = 'Match editor'
    attrs=(
        ('name','input','Title',100,{'charlimit':20}),
        ('music','listsel','Music',200,{'values':['']+sorted(olistdir(database['music_path']))}),
        ('scripts','inputlist','Scripts',200,{'add':True,'menu':{'type':'script'}}),
        )

class MatchEditorUI(EditorUI,SceneUI):
    CanvasEditor=MatchCanvasEditor
    def __init__(self,screen,matchdata,**kwargs):
        self.soundmaster = EditorSM(self)
        self._screen=screen
        views=kwargs.get('matchview',{})
        self.scene = match = MatchEditor(self,data=matchdata,view=views)
        SceneUI.__init__(self,**kwargs)
        #self.scene is the generic name for the main handler, allows compatibility
        #between all the types of scenes

        if self.statusmenu():
            smenu=[('Menu',self.statusmenu)]
        else:
            smenu=False
        wintypes=kwargs.pop('wintypes',dict((  ('statusbar',lambda e: StatusBar(e,menu=smenu)),
                        ('nodelist',lambda e,t=match.canvas.handler:NodeList(e,t)),
                        ('sidepanel',lambda e,t=match.canvas:SidePanel(e,t)),
                        ('nodepanel',lambda e,t=match.canvas: MatchNodePanel(e,t)),
                        ('linkpanel',lambda e,t=match.canvas: MatchLinkPanel(e,t)),
                        ('actorpanel',lambda e,t=match.cast: ActorMatchPanel(e,t)),
                        ('matchpanel',lambda e,t=match.data: MatchPanel(e,t,itemwrite=True)),
                        ('placepanel',lambda e,t=match.data: SettingPanel(e,t,itemwrite=True)),
                    )))
        sidetypes=kwargs.pop('sidetypes',('nodepanel','linkpanel','actorpanel','matchpanel','placepanel'))


        super(MatchEditorUI, self).__init__(screen,None,wintypes=wintypes,sidetypes=sidetypes,**kwargs)

#        self.layers.insert(0,match.cast)
        self.layers.append(match)

    @property
    def match(self):
        return self.scene

    @property
    def components(self):
        return (self.match,)+self.match.components

    def make_dependencies(self):
        BasicUI.make_dependencies(self)
        user.evt.set_handle(self.match)
        self.match.make_dependencies()
        deplist=(
            (self,self.match.canvas.handler),
            (self,self.match.cast),
            (self,self.match),
            (self,self.match.data),
        )
        for d in deplist:
            self.depend.add_dep(*d)
        if self.window['statusbar']:
            self.depend.add_dep(self.window['statusbar'],user)

    def react(self,evt):
        super(MatchEditorUI, self).react(evt)
        if 'start_match' in evt.type :
            match=self.match
            views={'canvas':match.canvas,'cast':match.cast.view,'setting':match.setting.view}
            for v in views.values()+[match.canvas.handler]:
                try:
                    v.unhover()
                    v.unselect()
                except:
                    pass
            ui=MatchUI(self._screen,match.data,matchview=views,game_ui=self.game_ui ,editor_ui=self)
            handled= user.set_ui( ui,False)
            return handled

    def input_menu(self,typ,output_method,**kwargs):
        if typ=='ethos':
            return self.ethos_effect_maker(output_method,**kwargs)
        elif typ=='cflags':
            return self.flag_maker(output_method,**kwargs)
        elif typ=='nscript':
            kwargs.setdefault('class',ConvNodeScript)
            return self.item_script_maker(output_method,**kwargs)
        elif typ=='lscript':
            kwargs.setdefault('class',ConvLinkScript)
            return self.item_script_maker(output_method,**kwargs)
        elif typ=='talent':
            return self.talent_maker(output_method,**kwargs)
        elif typ=='actreac':
            return self.actor_react_maker(output_method,**kwargs)
        elif typ=='script':
            return self.script_maker(output_method,**kwargs)
        elif typ=='screffect':
            return self.script_effect_maker(output_method,**kwargs)
        elif typ=='scrcond':
            return self.script_cond_maker(output_method,**kwargs)
        else :
            return super(MatchEditorUI, self).input_menu(typ,output_method,**kwargs)

    def ethos_effect_maker(self,output_method,**kwargs):
        flist=(('name','input'),
            ('res','arrowsel',{'values':('face','terr','path','prox')}),
            ('val', 'drag',{'minval':-1.0,'maxval':1.0}),
            ('target','arrowsel',{'values':['claimer','hearer']+self.match.actors}),
            )
        kwargs.setdefault('title','Ethos effect:')
        self.maker_menu(flist,output_method,EthosEffect,**kwargs)

    def item_script_maker(self,output_method,**kwargs):
        klass=kwargs.pop('class',ConvNodeScript)
        flist=(
            ('name','input',{'legend':'Caoy','width':200}),)
        for i in klass.dft:
            if hasattr(klass,i+'s'):
                flist+= (i,'arrowsel',{'values':getattr(klass,i+'s')} ),
        flist+=(
            ('logic','input',{'legend':'Logic','width':300}),
            ('conds','inputlist',{'legend':'Add conds','width':200,'add':True,'menu':{'type':'scrcond'}}),
            ('effects','inputlist',{'legend':'Effects','width':200,'add':True,'menu':{'type':'screffect'}}),
            )
        self.maker_menu(flist,output_method,klass,**kwargs)

    def convtest_maker(self,output_method,**kwargs):
        #OBSOLETE (?)
        if kwargs.get('script',False):
            inopts={'width':200}
            kwargs.setdefault('title','Call script:')
        else:
            inopts={'wrap':True,'height':140,'width':200}
            kwargs.setdefault('title','Quote:')
        flist=()
        klass=kwargs.pop('class',ConvTest)
        for i in klass.dft:
            if hasattr(klass,i+'s'):
                flist+= (i,'arrowsel',{'values':getattr(klass,i+'s')} ),
        #flist+=('val','input',inopts),
        self.maker_menu(flist,output_method,klass,**kwargs)

    def flag_maker(self,output_method,**kwargs):
        ref=kwargs.pop('val',None)
        klass=CFlag
        if not isinstance(ref,klass):
            #caller=kwargs['caller']
            ref=klass()
            #ref=klass(caller.ref,caller.data)
        flist=(
            ('val','arrowsel',{'values':ref.defaults,'add':True}),
            ('info','input',{}),
            #('iter','arrowsel',{'values':('always',0,1,2,3,4)}),
            #('conds','inputlist',{'legend':'Conditions','width':200,'add':True,'menu':{'type':'scrcond'}}),
            #('effects','inputlist',{'legend':'Effects','width':200,'add':True,'menu':{'type':'screffect'}}),
            )
        kwargs.setdefault('title','Conversation flag:')
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)

    def script_maker(self,output_method,**kwargs):
        flist=(
            ('name','input',{'legend':'Name','width':200}),
            ('iter','arrowsel',{'values':('always',0,1,2,3,4)}),
            ('logic','input',{'legend':'Logic','width':300}),
            ('conds','inputlist',{'legend':'Conditions','width':200,'add':True,'menu':{'type':'scrcond'}}),
            ('effects','inputlist',{'legend':'Effects','width':200,'add':True,'menu':{'type':'screffect'}}),
            )
        kwargs.setdefault('title','Script:')
        self.maker_menu(flist,output_method,Script,**kwargs)

    def script_cond_maker(self,output_method,**kwargs):
        klass=MatchScriptCondition
        ref=kwargs.pop('val',None)
        if not isinstance(ref,klass):
            ref=klass()
        flist=(
            ('name','input',{'legend':'Name','width':200}),
            ('typ','toggle',{'templates':ref.templates}),
            )
        kwargs.setdefault('title','Script condition:')
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)

    def script_effect_maker(self,output_method,**kwargs):
        klass=MatchScriptEffect
        ref=kwargs.pop('val',None)
        if not isinstance(ref,klass):
            ref=klass()
        flist=(
            ('name','input',{'legend':'Name','width':200}),
            ('typ','toggle',{'templates':ref.templates}),
            )
        kwargs.setdefault('title','Script effect:')
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)

    def talent_maker(self,output_method,**kwargs):
        flist=(('name','input'),)
        for i in MatchGraph.Node.genres:
            flist+=(  (i, 'drag',{'minval':.0,'maxval':1.0,'legend':i}),)
        kwargs.setdefault('title','Talent:')
        self.maker_menu(flist,output_method,Talent,**kwargs)

    def actor_react_maker(self,output_method,**kwargs):
        flist=(('agree','arrowsel',{'values':ActorReact.agrees} ),
            ('emotion','arrowsel',{'values':ActorReact.emotions} ),
            ('event','arrowsel',{'values':ActorReact.events} ),
            ('text','input',{'width':200,'height':200})
            )
        kwargs.setdefault('title','Reaction:')
        self.maker_menu(flist,output_method,ActorReact,**kwargs)

    def graph_maker(self,output_method,**kwargs):
        flist=(('N','drag',{'legend':'Nodes','minval':0,'maxval':100,'unit':1}),
            ('k', 'drag',{'legend':'k','minval':0,'maxval':1.0,'showval':True}),
            ('grammar','arrowsel',{'values':MatchGraph.Props.grammars} )
            )
        kwargs.setdefault('title','Graph properties:')
        self.maker_menu(flist,output_method,MatchGraph.Props,**kwargs)


    def statusmenu(self):
        m=self.match
        lams=lambda: self.save_menu('match',m.save_to_file,default=m.data.name)
        newmatch=lambda :self.graph_maker(lambda e: m.renew(graph=e))
        laml=lambda: self.load_menu('match',m.set_from_file,new=newmatch)
        struct=('Save match',lams),('Load match',laml)
        if m.cast.actors:
            struct +=('Start match',lambda e=None: m.signal('start_match')),

        lamg=lambda:m.data.txt_export(filename=m.data.name)
        lami=lambda e:m.txt_import(filename=e)
        struct+=('Renew graph',lambda :self.graph_maker(lambda e: m.renew_graph(None,e))),
        struct+=('Export match as text',lamg),
        struct+=('Import match from text',lambda:self.load_menu('match',lami,ext='.arc.txt') ),
        if self.game_ui :
            #game=self.game_ui.game
            #lams=lambda: self.save_menu('game',game.save_to_file,default=game.data.name)
            #struct+= (('Save game',lams),
            struct+=('Return to game',self.return_to_game),
        else:
            struct+= ('Exit',lambda: self.confirm_menu(self.return_to_title,pos='center',
                legend='Exit to title screen?') ),
        return struct

    def return_to_game(self):
        fopen('logs/.editor_last','w')
        user.set_ui(self.game_ui,False, no_launch=True )

    def return_to_title(self):
        self.match.save_to_file('archive/last.dat')
        user.ui.game_ui.goto('title')

    def keymap(self,event):
        handled=False
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_s :
                #try:
                    #m=self.game_ui.game
                    #m.save_to_file(m.data.name)
                #except:
                m=self.match
                m.save_to_file(m.data.name)
                user.set_status('Saved as '+m.data.name)
                handled=True
        if event.key==pg.K_F9:
            self.match.signal('start_match')
        return handled or EditorUI.keymap(self,event)

class MatchSM(BasicSM):
    def receive_signal(self,signal,*args,**kwargs):
        sgn=signal.type
        if 'next' in sgn:
            return self.play('load')


class MatchUI(BasicUI,SceneUI):
    external=False
    name='matchUI'
    def __init__(self,screen,matchdata,**kwargs):
        self.soundmaster = MatchSM(self)
        self._screen=screen
        views=kwargs.get('matchview',{})
        self.scene=MatchPlayer(self,data=matchdata,view=views)
        SceneUI.__init__(self,**kwargs)
        BasicUI.__init__(self,screen,**kwargs)
        screen=self.screen
        self.layers.append(self.match)
        #if self.game:
            #self.layers.append(self.game)

        if self.statusmenu():
            smenu=[('Menu',self.statusmenu)]
        else:
            smenu=False

        wintypes=kwargs.pop('wintypes',
            (  ('statusbar',lambda e:StatusBar(e,menu=smenu), ('topleft','0,0') ),
                ('dialbox',DialBox,('midbottom','self.rect.midbottom')),
                ('turnbox',TurnBox, ('center','self.rect.center[0],70')),
                ('actionlist', ActionList,('topleft','self.window["turnbox"].rect.topright')),
            ))

        for z in wintypes:
            i,j,k=z
            j=j(self)
            self.window[i]=j
            self.view[i]=self.store[i]=True
            setattr(j.rect,k[0],eval(k[1]))
            self.pos[j]=j.rect.topleft
            self.group.add(j)
        self.hide('actionlist')
        self.hide('dialbox')

    @property
    def match(self):
        return self.scene

    def launch(self):
        self.make_dependencies()
        self.match.start_match()
        self.launched=True
        #self.subgraph_view()
    @property
    def components(self):
        return (self.match,)+self.match.components

    def make_dependencies(self):
        BasicUI.make_dependencies(self)
        user.evt.set_handle(self.match)
        self.match.make_dependencies()
        deplist=(
            (self,self.match.canvas.handler),
            (self,self.match.cast),
            (self,self.match),
            (self,self.match.data),
            (self.window['statusbar'], user),
            (self.window['turnbox'], self.match),
            (self.window['turnbox'], self.match.data),
            (self.match,self.window['turnbox']),
            (self.window['actionlist'], self.match),
            (self.window['actionlist'], self.match.data),
            (self.window['dialbox'], self.match),
            (self.window['dialbox'], self.match.data),
        )
        [self.depend.add_dep(*d) for d in deplist]

    def react(self,evt):
        source=evt.source
        if self.name==source:
            return False
        sgn=evt.type
        super(MatchUI, self).react(evt)
        if 'return_to_editor' in sgn :
            #if self.editor_ui:
                #return user.set_ui(self.editor_ui)
            #TODO:solve problems with passing views
            match=self.match
            for act in match.actors:
                a = match.cast.view.icon[act]
                a.rm_state('disabled')
                a.set_state('idle')
            #views={'canvas':match.canvas,'cast':match.cast.view,'setting':match.setting.view}
            views={}
            ui=MatchEditorUI(self._screen,match.data.parent,matchview=views,
                game_ui=self.game_ui)
            user.kill_ui(self.editor_ui)
            return user.set_ui(ui)
        elif '_ui' in sgn:
            pos=('statusbar','turnbox','actionlist')
            if 'hide' in sgn:
                if evt.args[0] in pos:
                    self.hide(evt.args[0])
                else:
                    [self.hide(i) for i in pos]
            elif 'show' in sgn:
                if evt.args[0] in pos:
                    self.show(evt.args[0])
                else:
                    [self.show(i) for i in pos]
            elif 'anim' in sgn:
                [self.window[i].set_anim(evt.args[0]) for i in pos]

        return False


    def event(self,event,**kwargs):
        classic=list(ergonomy['viewables'])
        idx=classic.index('statusbar')
        wseq=kwargs.pop('wseq',classic[:idx]+['turnbox','actionlist','dialbox']+classic[idx:])
        return super(MatchUI, self).event(event,wseq=wseq,**kwargs)

    def save_state(self,savename):
        self.game_ui.game.gamestate.node_state[self.match.data.parent.name+database['match_ext']]=self.match.data
        self.game_ui.game.save_state(savename)

    def statusmenu(self):
        struct=()
        #if self.editor_ui:
               # ('Toggle dialog box', self.trigger_dialbox),
        if self.game_ui and hasattr(self.game_ui.game,'gamestate'):
            game=self.game_ui.game
            sm=self.save_state
            struct+=('Save', lambda s=sm,d=game.gamestate.name:user.ui.save_menu('save',s,default=d)),
        #if database['demo_mode']:
            #struct+=('Help',self.demo_help),
            #if self.soundmaster.mute:
                #fix='on'
            #else:
                #fix='off'
            #struct+=('Switch audio '+fix,self.audio_switch),
        if not self.editor_ui:
            struct+=(
                ('Exit',self.return_to_title),)
        else:
            struct+=('Return to editor', self.match.return_to_editor),
        return struct

    def audio_switch(self):
        self.soundmaster.trigger()
        user.music.trigger()

    def return_to_title(self):
        user.ui.game_ui.goto('title')

    def general_menu(self,event=None):
        struct=()
        for l in self.layers :
            struct+=tuple(l.menu(event))
        if struct:
            #if 'target' in kwargs:
                #tgt=kwargs['target']
                #pos=self.abspos(tgt)+array(tgt.rect.size)/2
                #kwargs['pos']=pos
            self.float_menu(struct,oneshot=True)#,**kwargs)

    def keymap(self,event):
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_d and database['edit_mode'] :
                user.debug_mode=1-user.debug_mode
                print 'Debug:', user.debug_mode
                return True
            if event.key==pg.K_h:
                self.demo_help()
                return 1

        if event.key==pg.K_ESCAPE:
            if not self.window['floatmenu']:
                self.float_menu(self.statusmenu(),pos='center')
            else:
                self.close('floatmenu')
            return 1

        if user.debug_mode:
            if event.key==pg.K_p:
                print 'Debug: add pathos'
                self.match.cast.set_info(self.match.active_player,'path',.2)
                return 1
        if event.key==pg.K_F9:
            if self.editor_ui:
                return self.match.return_to_editor()
        return self.match.keymap(event)

    def trigger_dialbox(self):
        if self.view['dialbox']:
            self.hide('dialbox')
        else:
            self.show('dialbox')
            self.window['dialbox'].refresh()




class DialBox(Window):
    fixsize=True
    scrollable='v'
    name='dialbox'
    def __init__(self,interface,**kwargs):
        size =graphic_chart['dialbox_size']
        Window.__init__(self,interface,size,alpha=graphic_chart['window_hover_alpha'],**kwargs)
        self.add('text',val='Starting match',w=self.active_rect.w,wrap=True)
        self.update()

    def add_message(self,txt):
        #,fixsize='h'
        self.add('text',val=txt,w=self.active_rect.w,wrap=True,maxlines=None,hyper=ergonomy['dialbox_hyperlinks'])
        self.update()
        #self.set_offset('max',1)

    def react(self,evt):
        if not (self.name in self.parent.view and self.parent.view[self.name]):
            return False
        sgn=evt.type
        m=self.interface.match
        if 'batch' in sgn and evt.state==2 and evt.actor==m.active_player:

            #self.add_message(m.transcript[m.batchs[m.turn][-1]])
            #print m.cast.get_info(m.active_player,'transcript')
            #self.add_message(dict(m.cast.get_info(m.active_player,'transcript'))[evt] )
            #print 'Receiving', evt, id(evt),evt.make_transcript(m)
            self.refresh()#add_message(evt.make_transcript(m) )
        if 'next_player':
            self.refresh()

    def refresh(self):
        m=self.interface.match
        self.clear()
        msg=''
        for turn in range(1,m.turn+1):
            for batch in m.batchs[turn]:
                #if batch.actor == m.active_player:
                #self.add_message(m.transcripter.make_transcript(batch,m,m.active_player))
                msg+=m.transcripter.make_transcript(batch,m,m.active_player)+'\n' #obsolete
        self.add_message(msg)
        self.update()
        self.set_offset('max',1)

class TurnBox(Window):
    name='turnbox'
    def __init__(self,interface,**kwargs):
        size =graphic_chart['turnbox_size']
        Window.__init__(self,interface,size,alpha=graphic_chart['window_hover_alpha'],**kwargs)
        self.turn=self.add('text',pos=(0,0))
        self.actor=self.add('text',pos=(0,1))
        self.timetxt=self.add('text',val='Time left:',pos=(1,0))
        self.time_left=self.add('gauge',val=1.,pos=(1,1),w=90)
        self.perf=self.add('text',val='Perform',pos=(2,0),selectable=True,
            output_method=lambda :self.signal('perform_queue'),tip='Perform all planned actions.' )
        self.finish=self.add('text',val='End turn',pos=(2,1),selectable=True,
            output_method=self.finish ,tip='Let others speak and resplenish your time.')
        self.refresh()

    def finish(self):
        match=self.parent.match
        if match.queue:
            return self.interface.confirm_menu(lambda :self.signal('next_player'), legend='Finish turn without performing?' )
        if match.time_left>0:
            return self.interface.confirm_menu(lambda :self.signal('next_player'), legend='Finish turn?' )
        return self.signal('next_player')


    def react(self,evt):
        sgn=evt.type
        if 'turn' in sgn or 'queue' in sgn or 'player' in sgn:
            self.refresh()
        if 'overtime_denied' in sgn:
            self.timetxt.set_anim('blink',color='r',len=ANIM_LEN['long'])

    def refresh(self):
        match=self.parent.match

        if match.controller.get(match.active_player,None)!='human':
            self.perf.set_state('disabled')
            self.finish.set_state('disabled')
        else:
            self.finish.rm_state('disabled')
            if match.queue :
                self.perf.rm_state('disabled')
            else :
                self.perf.set_state('disabled')

        turn='Turn '+str(match.turn)
        if turn!= self.turn.val :
            self.turn.val= turn
            self.turn.redraw()
        self.time_left.set_val(match.time_left,max=match.time_allowance,neg=match.time_cost)
        if match.time_cost > match.time_left:
            self.timetxt.set_state('negative')
            self.timetxt.redraw()
        else :
            self.timetxt.rm_state('negative')
            self.timetxt.redraw()
        name='Actor: ' + match.cast.label(match.active_player,'name')

        if self.actor.val != name :
            self.actor.val=name
            self.actor.redraw()
        self.update()


class ActionList(Window):
    name='actionlist'
    fixsize=False
    def __init__(self,interface,**kwargs):
        maxsize=graphic_chart['actionlist_maxsize']
        size =graphic_chart['actionlist_size']
        alpha=graphic_chart['window_hover_alpha']
        Window.__init__(self,interface,size,maxsize=maxsize,alpha=alpha,**kwargs)
        self.list=False

    def react(self,evt):
        sgn=evt.type
        match=self.parent.match
        if match.controller.get(match.active_player,None)!='human':
            self.interface.hide(self.name)
        elif 'queue' in sgn:
            n=self.name
            w=self.parent.match.queue
            if not self.interface.view[n] and w :
                self.interface.show(n)
                self.set_anim('appear',len=ANIM_LEN['short'])
            if self.interface.view[n] and not w:
                if self.interface.launched:
                    self.set_anim('disappear',len=ANIM_LEN['short'],affects=[self])
                else:
                    self.interface.hide(n)
        if 'anim_stop' == sgn:
            if evt.args[0].anim=='disappear':
                self.interface.hide(self.name)


    def refresh(self):
        self.clear()
        queue=self.parent.match.queue
        if not queue:
            self.interface.hide(self.name)
            return False
        v=0
        self.namefield={}
        self.okfield={}
        self.cancelfield={}
        for evt in queue :
            #Locate if click on name
            if hasattr(evt,'item'):
                tgt=evt.item
            else:
                tgt=evt.pos
            meth=lambda t=tgt:self.parent.match.canvas.handler.center_on(t)
            self.namefield[evt]=self.add('text',val=evt.desc, pos=(v,1),
                selectable=1,output_method=meth)
            self.add('blank',width=30, pos=(v,2))
            #Perform
            pmeth=lambda ee=evt:self.parent.match.perform_single(ee)
            self.okfield[evt]= self.add('icon',val='ok',selectable=1,
                mouseover='Perform Action',
                 output_method=pmeth,pos=(v,3))
            #Cancel
            cmeth=lambda ee=evt:user.evt.undo(ee.wrapper)
            self.cancelfield[evt]= self.add('icon',val='cancel',
                mouseover='Cancel Action', selectable=1,
                output_method=cmeth, pos=(v,4))

            v+=1
        return True


    #def evt_click(self,evt):
        #OBSOLETE
        #struct=()
        #struct+=('Perform',self.parent.match.perform_queue ),
        #struct+=('Locate', ),
        #struct+=('Cancel',lambda e=evt:user.evt.undo(e.wrapper)),
        #self.list.unselect()
        #return self.parent.float_menu(struct,oneshot=1)


class GraphMenu(DragWindow):
    #Floating menu to pick a graph
    title = 'Graph menu'
    name='graphmenu'
    ref=None
    handler = None
    scrollable='v'

    def __init__(self,interface,infosource=None,**kwargs):
        size =graphic_chart['float_base_size']
        kwargs.setdefault('maxsize',array(array(interface.screen.get_rect().size)*.75,dtype='int'))
        DragWindow.__init__(self,kwargs.pop('dragarea',interface.screen),interface,size,**kwargs)
        self.clear()
        self.output_method=kwargs.get('output_method',self.set_ref)
        self.handler=infosource
        self.owner='General'
        self.make()

    @property
    def data(self):
        if hasattr(self.handler,'data'):
            return self.handler.data
        else :
            return self.handler

    def set_ref(self,g):
        self.ref=g

    def clear(self):
        DragWindow.clear(self)
        self.interface.depend.rem_dep(self,self.handler)
        self.interface.depend.rem_dep(self,self.data)
        self.list=None

    def make_dependencies(self):
        self.interface.depend.add_dep(self,self.handler)
        self.interface.depend.add_dep(self,self.data)

    def make(self,**kwargs):
        self.clear()
        self.make_dependencies()
        v=0
        self.add('text',val=self.title,pos=(v,0),width=100,height=30)
        self.add('text',val='Close',pos=(v,1),width=50,selectable=True,
            output_method=lambda e=self.name:self.interface.close(e))
        actors= self.data.cast.actors
        actdict={a.name:a for a in actors }
        actdict['General']='General'
        own=self.owner
        if own=='General':
            val=own
        else:
            val=own.name
        self.ownsel=self.add('arrowsel',val=val,values=['General']+[a.name for a in actors],
            output_method=lambda e:self.set_owner(actdict[e]),colspan=2)
        if own=='General':
            struct=('Base',self.handler.canvas.graph ),
            if hasattr(self.data,'convgraph'):
                 struct+=('Conversation', self.data.convgraph ) ,
        elif own in actors:
            struct = ('Base', self.data.actorgraph[own] ),
            if hasattr(self.data,'actorsubgraphs'):
                struct+=tuple( (act.name, self.data.actorsubgraphs[own][act] ) for act in actors )
        v+=1
        self.list=self.add('list',val=struct, output_method =self.output_method,colspan=2)

    def set_owner(self,o):
        self.owner=o
        self.make()