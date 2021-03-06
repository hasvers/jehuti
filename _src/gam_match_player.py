# -*- coding: utf-8 -*-

# Game system for a single match


from gam_match import *

from gam_interaction import *

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

        self.controller=DataDict()

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
        self.data.actorsubgraphs=DataDict()#sparsemat(False)
        self.data.reactree=nx.DiGraph()
        for script in self.data.all_scripts():
            script.runs=0


    def make_relations(self,actor=None):
        #Proximity, ethos
        if not actor:
            for actor in self.cast.actors:
                self.make_relations(actor)
            return
        proxystart=DataDict()
        ainf=self.cast.get_info(actor)
        for other in self.actors:
            if other != actor:
                oinf = self.cast.get_info(other)
                proxystart[other.trueID]=self.ruleset.init_prox(actor,other)

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
        aid=actor.trueID
        subact=MatchGraph.Subgraph(self.data.actorgraph[aid],rule='None',precursors=(self.convgraph,))
        subact.owner=aid
        subact.import_from_parent(rule=irule)
        self.data.actorsubgraphs.setdefault(aid,DataDict())
        self.data.actorsubgraphs[aid][aid]=subact
        subact.name='Self'+actor.name
        #self.canvas.add_subgraph(subact,pos=1)
        for other in self.cast.actors:
            if other != actor:
                sub=MatchGraph.Subgraph(subact,rule='None')
                #TODO: consider how to import what an actor initially thinks of another's beliefs
                orule = lambda e, a=actor,o=other: self.ruleset.actor_othergraph_init_rule(a,o,e)
                sub.import_from_parent(rule=orule)
                self.data.actorsubgraphs[aid][other.trueID]=sub
                sub.name='Oth'+actor.name+':'+other.name
                #self.canvas.add_subgraph(sub,pos=1)
                sub.owner=aid #TODO: this is maybe dangerous: the owner of sub[act][oth] is act
        #print self.data.actorsubgraphs[aid][aid],self.canvas.layers



    def start_match(self):
        pg.event.set_allowed(30)
        try:
            if self.data.music:
                user.music.play(self.data.music)
        except:
            pass
        self.interact=InteractionModel(self)
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
            #FIRST TIME LOADING THE MATCH
            self.set_player(self.human,True)
            #self.set_player(self.actors[0])
            self.signal('set_player',self.active_player,affects=(self.data,self.cast.data))

            abatch={}
            for actor in self.actors:
                abatch[actor]=BatchEvt(actor=actor,affects=(self.canvas.active_graph,self.data))

            self.add_phase(self.make_start_script() )
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

    def make_start_script(self):
        '''Loop over nodes and links with flags that warrant initial events,
        and put everything into a script (easier to reverse and to track).'''
        script=None
        for act in self.actors:
            aid=act.trueID
            for item in (item for n,ls in
                            self.data.actorgraph[aid].links.iteritems()
                            for item in [n]+ls):
                eff=None
                flags=[f.val for f in self.data.actorgraph[aid].get_info(item,'cflags')]
                if 'Starter' in flags:
                    eff = MatchScriptEffect(**{'typ':'Action','target':item,
                        'actor':aid,'evt':'claim','info':'cost:0'})
                elif 'Include' in flags:
                    eff = MatchScriptEffect(**{'typ':'Graph','target':item,
                        'owner':aid,'subject':aid,'evt':'add','info':''})
                if eff:
                    if not script:
                        script=Script()
                    script.effects.append(eff)
        return script


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
                print 'Signalling player set to',self.active_player
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

        barycenter=tuple(arint(barycenter+newbar))

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
        if (c.data.owner==self.active_player.trueID or c.data==self.canvas.active_graph) and self.controller[c.data.owner]=='human':
            subject =None
            target=c.item
            for oact,sub in self.data.actorsubgraphs[c.data.owner].iteritems():
                if sub==c.data:
                    subject=oact
            if subject:
                color=self.cast.get_info(subject,'color')
                anim= lambda t=target:self.canvas.icon[target].set_anim('blink')
                user.ui.add_visual(anim)
                self.canvas.icon[target].call_emote('%c{}%{}%%'.format(color,txt))

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

        handled= user.keymap(event)
        if handled:
            return handled
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
        if event.key==pg.K_RETURN:
            self.perform_queue()
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
                r.dump_stats('logs/logqueue.dat')
            else:
                self.perform_queue()
            return True

        if 'claim' in sgn:
            if evt.state==2:
                claim=evt.evt
                inter=self.interact.make_script(claim,self)
                self.add_phase(inter)
                #inter.pass_events()
                #print inter.events
                #print inter.factors
        if 'select' in sgn :
            if self.cast in evt.affects() :
                # Select Actor
                if  'unselect' in sgn:
                    self.toggle_subgraph()
                elif  sarg[0]==self.active_player:
                    self.cast.unselect()
                else:
                    self.toggle_subgraph(sarg[0])
            if self.canvas in evt.affects():
                #Select node or link
                if not 'unselect' in sgn and sarg[0] :
                    #Possible claim
                    item = sarg[0].item
                    if  self.canvas.get_info(item,'claimed'):
                        return False
                    if (self.time_left<0 and not database['allow_overtime']):
                        user.set_mouseover('No time',anim='emote_jump',mode='emote',
                            ephemeral=1,color='r',anchor=self.canvas.icon[item])
                        self.parent.soundmaster.play('cancel')
                        self.signal('overtime_denied')
                        return False

                    #In case the game rules require to claim multiple items together
                    otherclaims=list(self.ruleset.claim_together(item,self))
                    for o in tuple(otherclaims):
                        if item in o.required:
                            #If another claimer (e.g. link) will contain item claim
                            otherclaims.append(item)
                            otherclaims.remove(o)
                            item=o

                    evt.add_state(2,pred=1)
                    nevt = ClaimEvt(sgn, self.active_player,item)
                    qevt=QueueEvt(nevt,self.data)
                    qevt.cues[0]="destroy"
                    user.evt.data.bind( ( evt,qevt))
                    for o in otherclaims:
                        nevt = ClaimEvt(sgn, self.active_player,o)
                        oevt=QueueEvt(nevt,self.data)
                        user.evt.data.bind( ( qevt,oevt) )
                    return True

        if 'ponder' in sgn:
            item = sarg[0].item
            cst=skwarg.get('cost',max(self.ruleset.pondermin,self.time_left-self.time_cost))
            nevt = ExploreEvt(sgn, self.active_player,pos=self.canvas.graph.pos[item],cost=cst)
            cevt=QueueEvt(nevt,self.data)
            user.evt.do(cevt)

        if 'jumpaction' in sgn:
            item = sarg[0].item
            tgtpos=self.canvas.graph.pos[item]
            srcpos=self.data.active_region[0]
            cst=skwarg.get('cost',self.ruleset.jumpcost(srcpos,tgtpos) )
            nevt = JumpEvt(sgn,actor= self.active_player,pos=tgtpos,cost=cst)
            cevt=QueueEvt(nevt,self.data)
            user.evt.do(cevt)


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
                ('%c(255,0,0,0)%Criticism%%',lambda a='criticism',s=act,t=tgt:self.make_speech_act(a,s,t),
                    'Criticism (Other Face)'),
                ('%c(255,0,0,0)%Doubt%%',lambda a='doubt',s=act,t=tgt:self.make_speech_act(a,s,t),
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
        '''Perform the whole queue.'''
        batches=[]
        for evt in self.queue:
            if not evt.wrapper.batch in batches:
                batches.append(evt.wrapper.batch)

        for batch in batches:
            self.perform_batch(batch)
        self.canvas.handler.unselect()
        self.signal('perform_queue')

    def perform_single(self,evt):
        '''Perform a queued event out of order, taking it out of its batch'''
        if not evt in self.queue:
            raise Exception("Cannot perform unqueued event",evt)
        evt.wrapper.rem_batch()
        evt.wrapper.set_batch(None,self)
        self.perform_batch(evt.wrapper.batch)

    def perform_batch(self,batch):
        '''Subfunction: perform a batch.'''
        dif=self.time_left- self.time_cost
        if dif <0 :
            rude=PolitenessEvt(batch,self.active_player,dif,type='overtime')
            batch.add_event(rude)
            user.evt.data.bind( (batch,rude) )
        user.evt.do(batch, self,1)

