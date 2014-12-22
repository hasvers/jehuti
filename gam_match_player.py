# -*- coding: utf-8 -*-

# Game system for a single match


from gam_match import *


class MatchPlayer(MatchHandler,PhaseHandler):
    name='matchplayer'
    handlername='Player'


    def __init__(self,*args,**kwargs):
        data=kwargs['data']
        if isinstance(data,MatchState):
            reloading=True
        else:
            reloading=False
            kwargs['data']=MatchState(data)
        MatchHandler.__init__(self,*args,**kwargs)
        #if self.parent:
            #size  =self.parent.screen.get_rect().size
        #else :
            #size=user.screen.get_rect().size
            #size =graphic_chart['screen_size']

        self.controller={}

        self.batchs={1:[]} # Event batchs list, by turn
        self.queue=[] #Events not yet executed and added to the list
        self.start_queue=['wait'] #Starter events


        self.time_cost=0.

        PhaseHandler.__init__(self)


        #if not hasattr(self.data, 'convgraph') or not self.data.convgraph:
            #self.data.convgraph=Convgraph(self.canvas.graph,rule='all')
        #self.make_beliefs()

        if not reloading:
            self.data.time_allowance=1.
            self.data.time_left=1.
            self.data.active_player=self.actors[0]
            self.make_relations()
            self.make_conv()
            self.is_reloading=False
        else:
            self.batchs[self.data.turn]=[]
            self.is_reloading=True
        self.cast.set_active(self.data.active_player)

    @property
    def time_left(self):
        return self.data.time_left
    @property
    def time_allowance(self):
        return self.data.time_allowance

    @property
    def turn(self):
        return self.data.turn

    @property
    def convgraph(self):
        return self.data.convgraph

    @property
    def active_player(self):
        return self.data.active_player



    def event(self,event,**kwargs):
        handled= MatchHandler.event(self,event,**kwargs)
        if event.type==30 and not user.paused:
            self.time+=1
        if not handled:
            self.advance_phase()
        return handled

    def menu(self,event,**kwargs):
        struct=()
        #struct+= ('Explore',self.make_explorer),

        for l in (self.cast,self.canvas.handler,self.setting):
            if l.menu(event):
                struct+=tuple(l.menu(event))

        return struct

    def return_to_editor(self):
        for c in (self.canvas.handler,self.cast.view,self.setting.view):
            c.unhover()
            c.unselect()
        self.clear_queue()
        self.clear_conv()
        self.cast.data.kill()
        self.signal('return_to_editor')
        user.music.stop()
        self.canvas.dft_graph_states = self.editor_state
        return True

    def make_conv(self):
        if self.convgraph is None:
            self.clear_conv()
            self.data.convgraph=Convgraph(self.canvas.graph,rule='all')

            self.make_beliefs()
        cv=self.convgraph
        #cv.transparent=True
        actors=self.cast.actors
        #for n in cv.nodes:
            #for act in actors:
                #fl=self.data.actorgraph[act].get_info(n,'cflags')
                #if fl and 'Starter' in fl :
                    #evt = ClaimEvt('Starter', act,n)
                    #self.start_queue.append(evt)
                    #user.evt.do(evt,self,2,ephemeral=True,handle=self)
                    #cf make_beliefs

    def clear_conv(self):
        #return 0

        self.clear_phase()
        if self.data.convgraph:
            self.data.convgraph.kill()
        self.start_queue=['wait']
        for i,j in self.data.actorsubgraphs.iteritems():
            for k,l in j.iteritems():
                l.kill()
        self.data.convgraph=None
        self.data.actorsubgraphs=sparsemat(False)
        self.data.reactree=nx.DiGraph()
        for script in self.data.all_scripts():
            script.runs=0


    def make_relations(self,actor=None):
        #Proximity, ethos
        if not actor:
            for actor in self.cast.actors:
                self.make_relations(actor)
            return
        proxystart={}
        ainf=self.cast.get_info(actor)
        for other in self.actors:
            if other != actor:
                oinf = self.cast.get_info(other)
                proxystart[other]=self.ruleset.init_prox(actor,other)

        self.cast.set_info(actor,'prox',proxystart)
        self.cast.set_info(actor,'path',0)
        self.cast.set_info(actor,'teri',0)
        self.cast.set_info(actor,'effects',{})

    def make_beliefs(self,actor=None):
        if not actor:
            for actor in self.cast.actors:
                self.make_beliefs(actor)
            return
        irule = lambda e, a=actor: self.ruleset.actor_selfgraph_init_rule(a,e)
        subact=MatchGraph.Subgraph(self.data.actorgraph[actor],rule='None',precursors=(self.convgraph,))
        subact.owner=actor
        subact.import_from_parent(rule=irule)
        self.data.actorsubgraphs[actor][actor]=subact
        subact.name='Selfgr'+actor.name
        #self.canvas.add_subgraph(subact,pos=1)
        for other in self.cast.actors:
            if other != actor:
                sub=MatchGraph.Subgraph(subact,rule='None')
                #TODO: consider how to import what an actor initially thinks of another's beliefs
                orule = lambda e, a=actor,o=other: self.ruleset.actor_othergraph_init_rule(a,o,e)
                sub.import_from_parent(rule=orule)
                self.data.actorsubgraphs[actor][other]=sub
                sub.name='Othgr'+other.name
                #self.canvas.add_subgraph(sub,pos=1)
                sub.owner=actor #TODO: this is maybe dangerous: the owner of sub[act][oth] is act
        #if actor==self.active_player:
            #self.canvas.set_layer(self.data.actorsubgraphs[actor][actor],0)
            #I dont know what the comments below refer to! (august 2013)
            #NB: this is useful so that the convgraph may be modified by Starter nodes Claim events taking place in make_conv
            #(the convgraph is attainable as a precursor of this layer)
            # #TODO : Clean this strange dependency

        #else:
            #self.canvas.set_layer(self.data.actorsubgraphs[actor][actor],-1 )


    def start_match(self):
        pg.event.set_allowed(30)
        try:
            if self.data.music:
                user.music.play(self.data.music)
        except:
            pass
        self.editor_state= deepcopy( self.canvas.dft_graph_states)
        self.canvas.dft_graph_states['idle']='hidden'
        for actor in self.actors:
            ctr=self.cast.get_info(actor,'control')
            if ctr =='AI':
                self.controller[actor]=AIPlayer(actor,self)
            elif ctr=='human':
                self.controller[actor]='human'
                self.human=actor

        for actor in self.actors:
            self.canvas.add_subgraph(self.data.actorsubgraphs[actor][actor],pos=len(self.canvas.layers))
            if self.controller[actor]=='human':
                for actor2 in self.actors:
                    self.canvas.add_subgraph(self.data.actorsubgraphs[actor][actor2],pos=1)
        act=self.data.active_player
        self.canvas.set_layer(self.data.actorsubgraphs[act][act],0)

        if not self.is_reloading:
            self.set_player(self.human,True)
            #self.set_player(self.actors[0])
            self.signal('set_player',self.active_player,affects=(self.data,self.cast.data))

            abatch={}
            for actor in self.actors:
                abatch[actor]=BatchEvt(actor=actor,affects=(self.canvas.active_graph,self.data))

            for e in self.start_queue:
                if e=='wait':
                    continue
                batch=abatch[e.actor]
                user.evt.do(e,self,2)
                batch.add_event(e)
                if 'claim' in e.type:
                    batch.add_event(e.decl)
                    batch.add_event(e.expl)
            for actor in self.actors:
                batch=abatch[actor]
                user.evt.do(batch,self,2)
        else:
            self.set_player(self.data.active_player,True,True,False)
            #self.set_player(self.actors[0])
            self.signal('set_player',self.active_player,affects=(self.data,self.cast.data))

        self.bary_queue=[]
        self.renew_barycenter(move=0,glide=0)
        self.start_queue=[]
        for c in (self.canvas.handler,self.cast.view,self.setting.view):
            c.unhover()
            c.unselect()

        change=1
        while change:
            change=self.advance_phase()

        self.test_scripts('start')
        self.renew_barycenter(move=1,glide=0)
        self.is_reloading=False

    def set_player(self,actor,nosignal=False,viewpoint=False,calc_time=True):
        subs=self.data.actorsubgraphs
        dft=self.canvas.dft_graph_states
        if self.active_player != actor:
            for i,j in subs[self.active_player].iteritems():
                try:
                    del dft[j]
                except:
                    pass
        if actor in self.actors:
            #infos = self.cast.get_info(actor)
            if calc_time:
                time=self.ruleset.time_allowance(actor)
                self.data.time_allowance= time
                self.data.time_left=time
            self.cast.set_active(actor)
            self.data.active_player=actor
            if self.controller[actor]=='human' or viewpoint:
                dft[subs[actor][actor]]='idle'
                self.canvas.set_layer(subs[actor][actor],0)
                self.canvas.handler.human_player=True
                # print self.data.actorsubgraphs[actor][actor].nodes
            else:
                dft[subs[self.human][actor]]='idle'
                dft[subs[self.human][self.human]]='ghost'
                #self.canvas.set_layer(subs[self.human][actor],0)
                self.canvas.handler.human_player=False
                #self.cast
            if not nosignal:
                self.signal('set_player',self.active_player,affects=(self.data,self.cast.data))
            if self.controller[actor]!='human' and self.controller[actor]:
                self.controller[actor].make_turn()



    def next_turn(self):
        #Old: execute whole queue before going to the next turn
        #[e.do(turn=self.turn) for e in self.queue ]
        self.data.turn+=1
        self.batchs[self.turn]=[]
        print 'next turn'
        #self.renew_barycenter(1)
        self.signal('new_turn')

    def next_player(self):
        print '\n Next player \n'
        self.clear_queue()
        act=self.actors.index(self.active_player)
        if act < len(self.actors)-1:
            act= self.actors[act+1]
        else :
            act=self.actors[0]
            self.next_turn()
        self.set_player(act)
        self.renew_barycenter()
        if self.controller[act]=='human':
            self.available_claims(act,1)


    def undo_prev_turn(self):
        if self.turn-1 in self.batchs :
            [e.undo() for e in self.batchs[self.turn-1].events]
        del self.batchs[self.turn]
        self.clear_queue()
        self.data.turn -=1

    def set_barycenter(self,barycenter,external=True,**kwargs):
        #print 'setting', barycenter
        radius=self.data.active_region[1]
        self.canvas.handler.set_circle(barycenter,radius,**kwargs)
        self.data.active_region=(barycenter,radius)
        if external:
            self.bary_queue.append( self.turn )

    def renew_barycenter(self,**kwargs):
        #print 'renewing', debug.caller_name(), kwargs
        radius=rint(self.ruleset.conv_radius(self.active_player))
        try:
            barycenter=self.data.active_region[0]
        except:
            barycenter=(0,0)
        evoked=[]
        pos=self.canvas.pos
        for n in self.convgraph.nodes:
            info=self.convgraph.get_info(n)
            if info['lastmention']:
                evoked.append((n,info['lastmention'],info['val'],array(pos[n])) )
        if not evoked:
            return False
        limit= self.turn-database['turn_memory']
        if self.bary_queue:
            limit= max(max(self.bary_queue),limit)
        evoktest = filter(lambda e:e[1]>limit,evoked)
        if evoktest:
            evoked=evoktest
        else :
            #if none in memory, retain only the last one
            #TODO: might change this, since here barycenter will change spontaneously even if not moving at all
            # due to forgetting things that are in plain sight
            if not self.bary_queue:
                evoked=[sorted(evoked,key=lambda e:e[1],reverse=True)[0]]
            else:
                evoked=[]
        evoked=sorted(evoked,key=lambda e:e[1],reverse=True)

        if evoked:
            barycenter=sum(i[3] for i in evoked  )/len(evoked)
        test = True
        pocket=[]
        newbar=array((0,0))
        while evoked and test:
            pocket.append(evoked.pop(0))
            totval=sum(i[2] for i in pocket)
            newbar=array( tuple(sum((pos[i[0]]-barycenter)[d]*i[2]/totval/(self.turn+1-i[1]) for i in pocket)  for d in (0,1) ))
            #if 1 or max(hypot(*(array(pos[i[0]])-newbar) ) for i in pocket) < radius  :
                #barycenter=newbar
            #else :
                #test = False
        barycenter+=newbar

        barycenter=tuple(array(barycenter,dtype='int'))

        #print 'renew barycenter', barycenter, radius, self.active_player, debug.caller_name()
        #print evoked, pocket
        self.canvas.handler.set_circle(barycenter,radius,**kwargs)
        self.data.active_region=(barycenter,radius)
        return True

    def available_claims(self,player=None,callscripts=True):
        barycenter,radius=self.data.active_region
        #returns nodes & links that can be claimed
        pos=self.canvas.pos
        if player is None:
            player=self.active_player
        actgraph=self.data.actorsubgraphs[player][player]
        unclaimed=[n for n in actgraph.nodes if not actgraph.get_info(n,
            'claimed') and not 'Req' in actgraph.get_info(n,'desc')]
        unclinks=[l for n in actgraph.links for l in actgraph.links[n] if not actgraph.get_info(l,
            'claimed') and not 'Req' in actgraph.get_info(l,'desc')]
        if not unclaimed and not unclinks:
            if callscripts:
                self.call_scripts('all_claimed_'+player.name) #TODO: previously add_phase
            loc,loclinks= (),()
        else:
            undist=sorted([ (n,hypot(*(pos[n]-array(barycenter)))) for n in unclaimed ],
                key=lambda e:e[1])
            loc=[]
            while undist and undist[0][1]<radius:
                loc.append(undist.pop(0))
            loclinks=[l  for l in unclinks if True in (hypot(*(pos[p]-array(barycenter))
                        )<radius for p in l.parents)]
            if not loc and not  loclinks:
                if callscripts:
                    self.call_scripts('loc_claimed_'+player.name) #TODO: previously add_phase
                #return (),()
        #print player,loc,loclinks
        return loc, loclinks

    def test_scripts(self,evt=None): #evt will serve discriminate scripts that may be called
        if hasattr(evt,'type'):
            tevt=evt.type
        else:
            tevt=evt
            evt=None
        if self.start_queue: #Do not run scripts during launch
            return
        if tevt=='start' or True in [ x in tevt for x in 'info','add','batch','polite']:
            for scr in self.data.all_scripts():
                if scr.test_cond(self,evt):
                    self.add_phase(scr)
                #if tevt=='start':
                    #print scr, id(scr), [(c,id(c),c.state) for c in scr.all_children(1) ]
            #if tevt=='start':
                #print '\n+++++++\n\n'
        self.advance_phase()

    def canvas_emote(self,c,txt,src):
        #c is an event, like a change or other
        if (c.data.owner==self.active_player or c.data==self.canvas.active_graph) and self.controller[c.data.owner]=='human':
            subject =None
            target=c.item
            for oact,sub in self.data.actorsubgraphs[c.data.owner].iteritems():
                if sub==c.data:
                    subject=oact
            if subject:
                color=self.cast.get_info(subject,'color')
                anim= lambda t=target:self.canvas.icon[target].set_anim('blink')
                user.ui.add_visual(anim)
                self.canvas.icon[target].call_emote('#c{}#{}##'.format(color,txt))

    def toggle_subgraph(self,actor=None):
        sub=self.data.actorsubgraphs
        dft=self.canvas.dft_graph_states
        act=self.active_player
        if self.controller[act]=='human':
            if  actor is None:
                for oth in self.cast.actors:
                    dft[sub[act][oth]]='hidden'
                dft[sub[act][act]]='idle'
                self.canvas.set_layer(sub[act][act],0)
                return True
            else:
                if act!= actor:
                    dft[sub[act][act]] = 'ghost'
                    dft[sub[act][actor]]='idle'
                    self.canvas.set_layer([sub[act][actor],sub[act][act]],0)
                return True

# SIGNALS AND EVENTS

    def keymap(self,event,**kwargs):
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key==pg.K_p:
                return user.screenshot()
            if  pg.key.get_pressed()[pg.K_LALT] and event.key==pg.K_v and database['edit_mode']:
                return user.trigger_video()
        if event.key == pg.K_TAB :
            if len(self.canvas.layers) > 1 :
                sub=self.data.actorsubgraphs
                index=None
                for idx, act in enumerate(self.cast.actors):
                    if self.canvas.active_graph==sub[self.active_player][act]:
                        index= idx
                if not index is None:
                    nxt=self.actors[(index+1)%len(self.actors)]
                if index is None or nxt==self.active_player:
                    self.toggle_subgraph()
                else:
                    self.toggle_subgraph(nxt)
                return 1
        return 0


    def react(self,evt):
        sgn=evt.type
        if not 'batch' in sgn:
            self.test_scripts(evt) #TODO: better than this:discriminate by evt type
        sarg=list(evt.args)
        skwarg=evt.kwargs
        if 'next_turn' in sgn :
            self.next_turn()
            return True
        if 'next_player' in sgn :
            self.next_player()
            self.test_scripts('start')
            return True
        if 'perform_queue' in sgn:
            if database['edit_mode']:
                profiler.runcall(self.perform_queue)
                r = pstats.Stats(profiler)
                r.sort_stats('time')
                r.dump_stats('prolog.dat')
            else:
                self.perform_queue()
            return True

        if 'select' in sgn :

            if self.cast in evt.affects() :
                # Select Actor
                if  'unselect' in sgn:
                    self.toggle_subgraph()
                elif sarg[0]!=self.active_player:
                    self.toggle_subgraph(sarg[0])
            if self.canvas in evt.affects():
                if not 'unselect' in sgn and sarg[0] :
                    item = sarg[0].item
                    if database['demo_mode']:
                        #prevent selecting node alone
                        if item.type=='node':
                            cand=[]
                            for l in self.canvas.active_graph.links[item]:
                                oth=[n for n in l.parents if n!= item][0]
                                if  self.canvas.get_info(oth,'claimed'):
                                    cand.append((self.canvas.get_info(oth,'lastmention'),l))
                            if cand:
                                cand=sorted(cand,key=lambda e:e[0])[-1]
                                item=cand[1]
                    if  self.canvas.get_info(item,'claimed'):
                        return False
                    if self.time_left<0 and not database['allow_overtime']:
                        user.set_mouseover('No time',ephemeral=1,color='r')
                        self.parent.soundmaster.play('cancel')
                        return False
                    evt.add_state(2,pred=1)
                    nevt = ClaimEvt(sgn, self.active_player,item)
                    cevt=QueueEvt(nevt,self.data)
                    cevt.cues[0]="destroy"
                    user.evt.data.bind( ( evt,cevt) )
                    return True

        if 'ponder' in sgn:
            item = sarg[0].item
            cst=skwarg.get('cost',max(self.ruleset.pondermin,self.time_left-self.time_cost))
            nevt = ExploreEvt(sgn, self.active_player,pos=self.canvas.graph.pos[item],cost=cst)
            cevt=QueueEvt(nevt,self.data)
            user.evt.do(cevt)

        if 'batch' in sgn and evt.state==1:
            self.prepared_batch(evt)

        if 'batch' in sgn and evt.state==2:
            self.received_batch(evt)

        #if 'decl' in sgn and evt.state=='2' and evt.item.type=='link':
            #newtruth=self.ruleset.logical_change()
            #nevt=ChangeInfos
            #user.evt.bind()

        if 'speechact' in evt.type:
            tgt=evt.args[0]
            act=self.active_player
            struct=(('Apology',lambda a='apology',s=act,t=tgt:self.make_speech_act(a,s,t),
                    'Apology (Self Face -> Other Face)'),
                ('Compliment',lambda a='compliment',s=act,t=tgt:self.make_speech_act(a,s,t),
                    'Compliment (Self Face -> Other Territory)'),
                ('Deference',lambda a='deference',s=act,t=tgt:self.make_speech_act(a,s,t),
                    'Deference (Self Territory -> Other Face)'),
                ('Promise',lambda a='promise',s=act,t=tgt:self.make_speech_act(a,s,t),
                    'Promise (Self Territory -> Other Territory)'),
                ('#c(255,0,0,0)#Criticism##',lambda a='criticism',s=act,t=tgt:self.make_speech_act(a,s,t),
                    'Criticism (Other Face)'),
                ('#c(255,0,0,0)#Doubt##',lambda a='doubt',s=act,t=tgt:self.make_speech_act(a,s,t),
                    'Doubt (Other Territory)'),
                )
            user.ui.float_menu(struct)

        if 'pathos_signal' in evt.type:
            item=evt.args[0].item
            #tgt=self.canvas.active_graph.owner #WRONG NOW BECAUSE OWNER subgraph[act][oth] is now act, not oth
            if self.cast.view.selected:
                tgt=self.cast.view.selected.actor
            else:
                tgt=self.canvas.active_graph.owner
            print  'pathos_signal',tgt
            act=self.active_player
            val=self.cast.get_info(act,'path')
            #print evt.type
            if tgt==act:
                cost=0
            else:
                cost=val
            cond=self.ruleset.truth_value(round(
                self.data.actorsubgraphs[act][act].get_info(item,'truth')))
            nevt = PathosEvt('pathos',act,item,cond,val,targets=tgt,cost=cost)
            cevt=QueueEvt(nevt,self.data)
            user.evt.do(cevt)

    def prepared_batch(self,playerbatch):
        '''Once a batch has been prepared by its actor,
        add reactions from other actors.'''
        reactree=self.data.reactree

        #print 'Received batch', playerbatch, playerbatch.events, playerbatch.root_events
        #playerbatch=BatchEvt([evt],actor=evt.actor, affects=self)
        self.batchs[self.turn].append(playerbatch)
        batchs={}
        if True in ['decl' in e.type for e in playerbatch.events]:
            reactree.add_node(playerbatch)
            for actor in self.cast.actors:
                if actor != playerbatch.actor  :

                    batch=BatchEvt([],actor=actor, affects=playerbatch.affects() )
                    interpret_batch=BatchEvt([],actor=playerbatch.actor, affects=playerbatch.affects() )
                    recevts=[e for e in playerbatch.rec_events if 'claim' in e.type]
                    sub= [s for e in recevts for s in e.subclaims]
                    for e in recevts :
                        if e in sub:
                            continue
                        #if not 'claim' in e.type:
                        #if True in [i in evt.type for i in ('interpret' , 'react', 'politeness' )]:
                            #do not react to reactions!
                            #continue
                        reac=ReactEvt(e.source,actor,e,**e.decl.kwargs) #transmit claimed truth to React
                        #user.evt.do(reac,self,2)
                        batch.states.node[1]['children_states'][reac]=2
                        batch.states.node[1]['priority'][reac]=2
                        batch.add_event(reac)
                        interp=InterpretEvt(e.source,interpret_batch.actor,reac)
                        #user.evt.do(interp,self,2)
                        interpret_batch.states.node[1]['children_states'][interp]=2
                        interpret_batch.states.node[1]['priority'][interp]=1
                        interpret_batch.add_event(interp)

                        reactree.add_edge(playerbatch,batch)
                        reactree.add_edge(batch,interpret_batch)

                        reactree.add_edge(e,reac) #In principle dispensable through reac.parent
                        reactree.add_edge(reac,interp)
                    #if reac.do(1,self):
                        #user.evt.pass_event(reac,self.cast,True) #TODO: hackish to use cast as caller
                        #self.batchs[self.turn][-1].add_event(reac)
                    #interp=InterpretEvt(evt.source,evt,actor,reac)
                    #actorbatch.add_event(interp)
                    #print 'reac/interp',id(batch),id(interpret_batch)
                    playerbatch.states.node[2]['children_states'][batch]=2
                    playerbatch.states.node[2]['priority'][batch]=2
                    playerbatch.states.node[2]['children_states'][interpret_batch]=2
                    playerbatch.states.node[2]['priority'][interpret_batch]=1
                    batchs[actor]=[batch,interpret_batch]
        if batchs or not playerbatch in reactree.nodes() or len(self.cast.actors)==1:
            #Don't run the batch before everybody has reacted to it
            user.evt.do(playerbatch,self,2)
            #for actor in self.actors:
                 #[user.evt.do(b,self,2)  for b in batchs.get(actor,[]) ]

    def received_batch(self,evt):
        '''Once a batch has been executed, make:
            - speech balloons.
            - visual effects.'''
        batch_evts=evt.rec_events
        reactree= self.data.reactree
        ultim=evt #Ultimate source of the batch
        while ultim in reactree.nodes() and reactree.predecessors(ultim):
            ultim= reactree.predecessors(ultim)[0]

        #TEXT
        if ultim==evt:
            #Initial claim = explicit part
            texter=TextMaker(self.data)
            actor=evt.actor
            ainf=self.cast.get_info(actor)
            gph=self.data.actorsubgraphs[actor][actor]
            clusters,semdata,txts=texter.batch_declaration(ainf,gph,evt)
            for clus,txt in zip(clusters,txts):
                self.add_balloon(txt,anchor= actor,source=ultim,show_name=1)
                for reac in reactree.successors(evt):
                    oact=reac.actor
                    oinf=self.cast.get_info(oact)
                    ogph=self.data.actorsubgraphs[oact][oact]
                    effects={}
                    effects.update(evt.effects)
                    for i,j in reac.effects:
                        effects.setdefault(i,0)
                        effects[i]+=j
                    txt=texter.reac_say(oinf, ogph,reac,cluster=clus,sem=semdata,eff=effects)
                    if txt:
                        self.add_balloon(txt,anchor= oact,source=ultim,show_name=1)
        #elif 0 and evt.actor==self.active_player:
            #if ultim in reactree.predecessors(evt):
            ##reacs
                #print ''#reac'
            #else:
                #for e in evt.events:
                    #if not 'interp' in e.type:
                        #continue
                    #act=e.parent.actor
                    #nact=self.cast.get_info(act)
                    ##print c, c.item, c.kwargs['agreement']
                    #ag=TextMaker(self.data).agreement_reaction(nact,e.kwargs['agreement'])
                    #if ag[0]=='"':
                        #anchor=act
                        #disp=1
                    #else:
                        #anchor='Narrator'
                        #disp=0
                    #self.add_balloon(ag,anchor= anchor,show_name=disp,source=ultim)

        for c in batch_evts:
            if 'add' in c.type and c.item.type in ('link','node') :
                #print 'inbatch add',c.item,c.data#,self.canvas.active_graph
                #print 'with children',[z.data for z in c.current_children()]
                if c.data==self.canvas.active_graph  and c.state>=1 :
                    target=c.item
                    if 'reac' in c.parent.type and c.parent.is_discovery:
                        if database['edit_mode']:
                            self.canvas_emote(c,'Discovery!',ultim)
                    #print 'match719==Adding', target,'|',c.data, c.state, self.canvas.handler.label(target)
            #if 0 and 'interp' in c.type and c.actor==self.active_player:
                #act=c.parent.actor
                #nact=self.cast.get_info(act)
                ##print c, c.item, c.kwargs['agreement']
                #ag=TextMaker(self.data).agreement_reaction(nact,c.kwargs['agreement'])
                #if ag[0]=='"':
                    #anchor=act
                    #disp=1
                #else:
                    #anchor='Narrator'
                    #disp=0
                #self.add_balloon(ag,anchor= anchor,show_name=disp,source=ultim)

            if 'change' in c.type :
                target=c.item
                if target.type=='node' and 'truth' in c.kwargs:
                    if database['edit_mode']:
                        print 'Match: Truth change', target, c.data, c.infos
                        self.canvas_emote(c,'Truth changed!',ultim)

                if target.type=='node' and  c.kwargs.get('claimed',False):
                    for eff in self.canvas.icon[target].effects.values():
                        anim=lambda e=eff:e.set_anim('blink',len=ANIM_LEN['medlong'])
                        user.ui.add_visual( anim)
        for t,val in evt.effects.iteritems():
            act=t[0]
            if hasattr(val,'keys'):
                val=val.values()[0]
            res=t[1]
            if t[1]=='prox':
                res='emp'

            if val<0:
                color=graphic_chart['text_color_negative']
                val=str(rftoint(val))
            else :
                color=graphic_chart['text_color_positive']
                val='+'+str(rftoint(val))

            self.cast.view.icon[act].call_emote(res.capitalize()+val,color=color)
        self.test_scripts(evt)
        self.renew_barycenter(move='empty')

        #Look for scripts called by claims
        #+Center on last item claimed (maybe not such a good idea)
        center_on=None
        for c in batch_evts:
            if not ('claim' in c.type and c.state==2):
                continue
            claim=c
            if claim.item.type=='node':
                center_on=claim.item

            items=[claim.item]
            if hasattr(claim.item,'parents'):
                items+=claim.item.parents
            for item in items:
                for call in self.canvas.get_info(item,'calls'):
                    if call.event_check(claim,item,self):
                        #print 'Calling:',call.val, item, item.name
                        self.call_scripts(call.val,src=evt)
                        #for sc in self.get_scripts(call=call.val):

        if center_on:
            self.canvas.handler.center_on(center_on)

    def make_speech_act(self,act,source,target):
        print 'MakeSpeechAct', act, 'from', source,'to', target
        if not hasattr(target,'__iter__'):
            target=target,
        dif=max(self.ruleset.speechactmin,self.time_left- self.time_cost)
        nevt = PolitenessEvt('speech_act',source,dif,type=act,targets=target,cost=dif,desc=act.capitalize())
        cevt=QueueEvt(nevt,self.data)
        user.evt.do(cevt)


    def clear_queue(self):
        for evt in tuple(self.queue):
            user.evt.go(evt.wrapper,0)
            #self.rem_queue(evt,nosignal=True)
        self.queue=[]
        self.canvas.handler.unselect()
        self.signal('clear_queue')

    def perform_queue(self):
        batches=[]
        for evt in self.queue:
            #print evt,evt.wrapper
            #user.evt.do(evt.wrapper, self,2)

            if not evt.wrapper.batch in batches:
                batches.append(evt.wrapper.batch)

        for batch in batches:
            dif=self.time_left- self.time_cost
            if dif <0 :
                rude=PolitenessEvt(batch,self.active_player,dif,type='overtime')
                batch.add_event(rude)
                user.evt.data.bind( (batch,rude) )
            user.evt.do(batch, self,1)

        self.canvas.handler.unselect()
        self.signal('perform_queue')
        #self.renew_barycenter()

