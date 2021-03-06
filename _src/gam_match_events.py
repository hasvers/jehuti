# -*- coding: utf-8 -*-
from gam_rules import *
from gam_canvas import *


class MatchEvent(LogicEvent):
    cost =0 #Speech time cost
    submitted_on_turn=False
    def __init__(self,source,*args,**kwargs):
        # The source is what triggered this event branch (signal, script, etc)
        for i in kwargs.keys() :
            if i=='cost':
                self.cost = kwargs.pop(i)
            if i=='turn':
                self.submitted_on_turn=kwargs.pop(i)
        Event.__init__(self,source,*args,**kwargs)

        self.add_state(2,pred=1)




class QueueEvt(MatchEvent):
    #Simple wrapper for any event that is queued (always changes state after wrapped event)
    desc='Queue'
    dft={
        'evt':None,
        'data':None,
        }


    def __init__(self,evt,data,**kwargs):
        self.inverted=kwargs.pop('inverted',False)
        if self.inverted :
            lab = 'unqueue_'
            self.desc= 'Remove'
        else :
            lab='queue_'
        self.desc += ' '+evt.desc
        self.infos=kwargs.pop('infos',{} )
        self.newbatch=kwargs.pop('newbatch',False)
        super(QueueEvt, self).__init__(evt.source,type=lab+evt.type,**kwargs)

        self.evt=evt
        self.add_sim_child(evt,priority=1)
        evt.wrapper=self

        self.data=data
        self.temp=[] #children that must be removed after each undo/redo cycle
        if self.inverted:
            self.state=1

    def affects(self):
        return (self.evt,self.data)



    def run(self,state,match,**kwargs):
        evt=self.evt
        if state ==1 and evt.state==1 :
            self.cost=evt.cost
            if evt in match.queue :
                return False
            #user.evt.pass_event(evt,match)
            match.time_cost+=evt.cost
            match.queue.append(evt)
#            if not kwargs.get('nosignal',False):
            #match.signal('add_queue')

            return True

        if state==0 and evt.state==0 :
            if not evt in match.queue:
                return False
            match.time_cost-=evt.cost
            match.queue.remove(evt)
            for c in evt.current_children():
                try:
                    match.queue.remove(evt)
                except:
                    pass

            #if not kwargs.get('nosignal',False):
            #    match.signal('rem_queue')
            return True

        if state==2 :
            match.data.time_left-=evt.cost
            match.time_cost-= evt.cost
            match.queue.remove(evt)
            for c in evt.current_children():
                try:
                    match.queue.remove(c)
                except:
                    pass

            if 'claim' in evt.type:
                self.batch.add_event(evt)   #If i do this, declaration is not in root_events
                self.batch.add_event(evt.decl)
                if hasattr(evt,'expl'):
                    self.batch.add_event(evt.expl)

                for f in evt.subclaims:
                    self.batch.add_event(f)
                    self.batch.add_event(f.decl)
                    if hasattr(f,'expl'):
                        self.batch.add_event(f.expl)
            elif True in [ i in evt.type  for i in ('expl','polit') ]:
                self.batch.add_event(evt)
            return True
        return False

    def prep_init(self,match,*args,**kwargs):
        self.batch=None
        if not self.newbatch: #look for valid batch in match queue
            for evt in match.queue:
                if evt.wrapper!=self and hasattr(evt.wrapper,'batch') and evt.wrapper.batch.actor==self.evt.actor:
                    self.set_batch(evt.wrapper.batch)
                    return True
        if not self.batch:
            self.set_batch(None,match)
            return True
        #self.states.node[2]['children_states'][evt]=1
        #self.states.node[1]['children_states'][evt]=0
        #self.states.node[0]['children_states'][evt]=0

        #user.evt.data.bind( (self,evt), {(self,evt):[(2,1),(1,0) ],(evt,self):[(1,2),(0,1) ] })
        #The version above is a double-bind, but now batch is the master so

        #self.states.node[2]['priority'][evt]=-1

    def prep_uninit(self,*args,**kwargs):
        self.rem_batch()

    def rem_batch(self):
        #In case I want to sever it from a batch
        evt=self.batch
        user.evt.data.unbind( (self,evt), {(evt,self):[ (0,1) ] })
        del evt.states.node[1]['children_states'][self]
        del evt.states.node[1]['priority'][self]
        self.batch=None

    def set_batch(self,evt=None,match=None):
        if evt is None:
            evt=BatchEvt([],actor=self.evt.actor, affects=(match.data))
        user.evt.data.bind( (self,evt), {(evt,self):[ (0,1) ] })
        evt.states.node[1]['children_states'][self]=2
        evt.states.node[1]['priority'][self]=1
        self.batch=evt


class NewReactEvt(MatchEvent): #OBSOLETE DUE TO gam_interaction
    desc ='React'

    #1)initial value of admitted node (new node in subgraph) may depend of convincing arguments
    #presented at the same time, and not only on proximity

    #2)Priority in reactions: offended overcomes other reactions, so that the others become
    #implicit (e.g. reaction to truth left unvoiced) and it is harder to know the offended person's real thoughts

    #=> 1 and 2 together: tradeoff between initial convinction being stronger if supported by \
    #arguments, and muddled reaction from many different sources, giving less information on the other's mental state


    def __init__(self,source,actor,batch,**kwargs):
        super(ReactEvt, self).__init__(source,**kwargs)
        self.type='react_evt'
        self.actor=actor
        self.batch=batch
        self.is_discovery=False

    def __str__(self):
        return '{} {} Discovery: {}  -> {}'.format(self.desc,self.actor,self.is_discovery)

class ReactEvt(MatchEvent): #OBSOLETE DUE TO gam_interaction

    desc ='React'

    dft={
        'actor':None,
        'parent':None,
        }


    def __init__(self,source,actor,event,**kwargs):
        super(ReactEvt, self).__init__(source,**kwargs)
        self.type='react_evt'
        self.actor=actor
        self.parent=event
        self.is_discovery=False
        self.subreact=[]


    def __str__(self):
        return '{} {} Discovery: {}  -> {}'.format(self.desc,self.actor,self.is_discovery,self.parent)

    @property
    def item(self):
        return self.parent.item

    def prep_init(self,match,**kwargs):
        #print 'react', self.actor, self.item
        act=self.actor
        evt=self.parent
        sinf = match.cast.get_info(act)
        try:
            received_truth = self.kwargs['truth']
        except:
            raise Exception('No truth {} {} {} {}'.format(act,evt,evt.args,evt.kwargs) )

        for c in evt.subclaims:
            sub=ReactEvt(c.source,act,c,**c.decl.kwargs)
            self.subreact.append(sub)
            self.add_sim_child(sub,priority=1)
            self.states.node[0]['priority'][sub]=-1

        interpreted_truth=believed_truth =None
        item= evt.item
        if item.type=='node':
            interpreted_truth= match.ruleset.perceive_truth(received_truth,sinf)
        subs=match.data.actorsubgraphs
        effects =[]
        if not match.data.actorgraph[act].contains(item):
            # Actor did not know this item
            self.is_discovery=True
            if item.type=='node':
                believed_truth, effects, agreement = match.ruleset.accept_truth(interpreted_truth,evt.actor,sinf)
                self.child_add(item,match.data.actorgraph[act],bias=(believed_truth-.5))
                self.kwargs['believed_truth']=believed_truth
            if item.type=='link':
                #TODO: test if known pattern
                agreement = +1

        else:
            if subs[act][act].contains(item):
                test= subs[act][act].infos.get(item,False)
                if test and test.get('claimed',False):
                    print 'Prep react to already claimed',item,act
                    return False
            if not self.is_discovery :
                #Actor previously knew this item (but it was still unclaimed)

                if item.type=='node':
                    believed_truth = match.data.actorgraph[act].get_info(item,'truth')
                    effects, agreement = match.ruleset.contrast_truth(interpreted_truth,believed_truth)
                    self.kwargs['believed_truth']=believed_truth
                if item.type=='link':
                    agreement = +1
        #print item, 'believed,received,interpreted',believed_truth,received_truth,interpreted_truth

        sao=subs[act][evt.actor] #other-subgraph
        saokwargs={'truth':interpreted_truth}
        self.child_add(item,subs[act][act],truth=believed_truth)
        if item.type=='node' and not self.is_discovery:
            pbias= interpreted_truth-match.ruleset.calc_truth(item,subs[act][act],sao,extrapolate=1,bias=0)
            #Perceived bias compared to what this actor would assume knowing the link HE knows
            #but with the truth values that he believes the other one has
            #print 'Reac: Received/perceived truth, perceived bias',received_truth, interpreted_truth, pbias
            saokwargs['bias']=pbias
        self.child_add(item,sao,**saokwargs)


        self.kwargs['agreement']=agreement
        self.effects=effects #Let the batch deal with them

        #for e in effects :
            #if e=='prox':
                ##print 'prox change',effects[e],'in',act,'about',evt.actor
                #val = match.cast.data.get_info(act,'prox')[evt.actor]
                #val+=effects[e]
                #eevt=ChangeInfosEvt(act,match.cast.data,prox={evt.actor:val},update=True)
                #self.add_sim_child(eevt)


    def prep_do(self,match,**kwargs):
        evt=self.parent
        item= evt.item
        if item.type=='node' and database['expl_on_react'] :
            eevt=ExploreEvt(self.source,self.actor,pos=match.canvas.graph.pos[item] )
            self.add_sim_child(eevt)

class InterpretEvt(MatchEvent):

    desc ='Interpret'

    dft={
        'actor':None,
        'parent':None,
        }


    def __init__(self,source,actor,event,**kwargs):
        super(InterpretEvt, self).__init__(source,**kwargs)
        self.type='interpret_evt'
        self.actor=actor
        self.parent=event
        self.is_discovery=False
        self.subinterp=[]


    def __str__(self):
        return '{} {} Discovery: {}  -> {}'.format(self.desc,self.actor,self.is_discovery,self.parent)

    @property
    def item(self):
        return self.parent.item

    def prepare(self,edge,match,*args,**kwargs):
        if edge[1] !=1:
            return False

        subs=match.data.actorsubgraphs
        item=self.item
        sinf = match.cast.get_info(self.actor)
        oact=self.parent.actor
        sao=subs[self.actor][oact]

        for subrec in self.parent.subreact:
            sub=InterpretEvt(self.source,self.actor,subrec)
            self.subinterp.append(sub)
            self.add_sim_child(sub,priority=1)
            self.states.node[0]['priority'][sub]=-1

        #print 'interpret',self.actor, oact, item
        if item.type=='node':
            rtruth=self.parent.kwargs['believed_truth']
            if self.parent.kwargs.get('explicit',True):
                #Explicit reaction: false perception can only affect intensity of opinion
                #but not revert it
                ptruth = match.ruleset.perceive_truth(rtruth,sinf)
            else:
                #Implicit reaction: add random noise in preception
                ptruth = match.ruleset.perceive_info(rtruth,sinf)

            pbias= ptruth-match.ruleset.calc_truth(item,subs[self.actor][self.actor],sao,extrapolate=1,bias=0)
            #Perceived bias
            #print 'Interpret: Received/perceived truth, perceived bias',rtruth, ptruth, pbias
            infokwargs={'truth':ptruth,'bias':pbias}
        else :
            infokwargs={}
        if  not sao.contains(item):
            self.child_add(item,sao,**infokwargs)
        elif item.type=='node' :
            self.child_chginfo(item,sao,**infokwargs)

        effects =[]
        if item.type =='node':
            effects, agreement = match.ruleset.contrast_truth(self.parent.kwargs['truth'],ptruth)
        else :
            agreement=1

        self.kwargs['agreement']=agreement
        #for e in effects :
            #if e=='prox':
                #print 'understood as prox change',effects[e],'in',oact,'about',self.actor
                #val = match.cast.data.get_info(oact,'prox')[self.actor]
                #val+=effects[e]
                #eevt=ChangeInfosEvt(act,match.cast.data,prox={evt.actor:val},update=True)
                #self.add_sim_child(eevt)

class LogicEvt(MatchEvent):
    #OBSOLETE!!!!!!! Now the canvas computes logical reactions

    #Logic impact of discovery of links or truth change of node
    #DO NOT CALL IF THE SITUATION IS EXACTLY AS BELIEVED BY RECEIVER
    #otherwise would be a double-count

    dft={
        'actor':None,
        'item':None,
        }


    desc ='Logic'
    def __init__(self,source,actor,item,**kwargs):
        super(LogicEvt, self).__init__(source,**kwargs)
        self.type='logic_evt'
        self.actor=actor
        self.item=item
        self.args=item,


    def __str__(self):
        return '{} {} {}'.format(self.desc,self.actor,self.item)

    def prep_do(self,match,*args,**kwargs):
        for i in (self.actor,match.data):
            if not i in self._affects:
                self._affects+=(i,)


        i=self.item
        act=self.actor
        #ainf=match.cast.get_info(act)
        graph=match.data.actorgraph[act]
        sub=match.data.actorsubgraphs[act][act]


        if i.type=='link':
            links=[i]
            if graph.get_info(i,'logic')[3]:
                ns=i.parents
            else:
                ns=[i.parents[0]]

        elif i.type=='node':
            links= sub.links[i]
            n=i
            ns=[n]

        for n,l in itertools.product(ns,links) :
            if n==l.parents[0] or graph.get_info(l,'logic')[3]:
                target=l.parents[1-l.parents.index(n)]
                #print 'doing link', l.parents, graph.get_info(l,'logic'), n
                truth=match.ruleset.calc_truth(target,graph,graph)
                prevtruth=sub.get_info(target,'truth')
                if prevtruth!=truth:
                    pass
                   # print 'Truth change',act,target,prevtruth,truth
                else :
                   # print 'No change'
                    continue

                self.child_chginfo(target,sub,truth=truth)
                if not sub.get_info(target):
                   # print act,'didnt know', target
                    raise Exception()
                if match.ruleset.truth_disagreement(truth,prevtruth):
                    print '#chain reaction'
                    self.add_sim_child(LogicEvt(self.source,act,target) )
                tinf=sub.get_info(target)
                owner=sub.get_info(target,'claimed')
                if not owner:
                    return
                actcause=world.get_object(owner)
                if act == actcause:
                    print 'Receiving logical consequence of own claim! (i.e. analyzing own react, not good)', act
                if tinf['claimed'] == act.trueID and act!=actcause and prevtruth != truth:
                    if match.ruleset.concede_test(act,actcause,tinf,prevtruth,truth):
                        print act, 'concedes', target, 'to', actcause
                        self.add_sim_child(ConcedeEvt(self,act,actcause,target))


class DeclareEvt(MatchEvent):
    desc ='Declare'

    dft={
        'actor':None,
        'item':None,
        }


    def __init__(self,source,actor,item,**kwargs):
        super(DeclareEvt, self).__init__(source,**kwargs)
        self.type='declare_evt'
        self.actor=actor
        self.item=item
        self.args=item,


    def __str__(self):
        return '{} {} {}'.format(self.desc,self.actor,self.item)

    def prepare(self,edge,match,*args,**kwargs):
        for i in (self.actor,match.data):
            if not i in self._affects:
                self._affects+=(i,)
        if edge[1] ==2:

            act=self.actor
            item=self.item
            subs=match.data.actorsubgraphs
            basetruth = subs[act][act].get_info(self.item, 'truth')

            self.child_add(item,match.convgraph,truth=basetruth)
            self.kwargs['truth']=basetruth
            self.child_chginfo(item,match.convgraph,lastmention=match.turn)

            return True
        return False

class ClaimEvt(MatchEvent):
    desc ='Claim'
    fixcost=None

    dft={
        'actor':None,
        'item':None,
        }

    def __init__(self,source,actor,item,**kwargs):
        if 'cost' in kwargs:
            self.fixcost=kwargs.pop('cost')
        super(ClaimEvt, self).__init__(source,**kwargs)
        self.type='claim_evt'
        self.actor=actor
        self.item=item
        self.args=item,
        self.subclaims=[]
        self._cost=0


    def __str__(self):
        return '{} {} {}'.format(self.desc,self.actor,self.item)

    @property
    def cost(self):
        if self.fixcost is None:
            return self._cost + sum(c.cost for c in self.subclaims)
        else:
            return self.fixcost

    @cost.setter
    def cost(self,value):
        self._cost=value

    def prep_init(self,match):
        if self.state>0 :
            return True
        evt=self

        item=evt.item
        iti = match.canvas.get_info(item)
        if type( iti['claimed'])==int or iti['claimed']==True :
            return False
        acti = match.cast.get_info(evt.actor)
        evt.cost= match.ruleset.claim_cost(item,iti,acti)
        evt.turn = match.turn
        for r in item.required:
            #Seems to work

            if match.canvas.get_info(r,'claimed'):
                continue
            c=ClaimEvt(evt.source,evt.actor,r)
            #if c.prep_init(match):
            self.add_sim_child(c,priority=2)
            self.states.node[0]['priority'][c]=-1
            self.subclaims.append(c)
            c.parent=self
            #evt.cost+=c.cost

        if item.type=='node' and database['expl_on_claim']:
            eevt=ExploreEvt(self.source,self.actor,pos=match.canvas.graph.pos[item] )
            self.add_sim_child(eevt)
            self.expl=eevt
            eevt.parent=self


#        self.signal(evt.type,'change_infos_canvas',evt.item,claimed=True)
        grp=match.data.actorsubgraphs[self.actor][self.actor]
        if grp.contains(item):
            self.child_chginfo(item,grp,1,0,claimed=True)
        else:
            self.child_add(item,grp,1,0,claimed=True)
        return True

    def prep_do(self,match,*args,**kwargs):
        if self.state>1 :
            return True
        evt=self
        item=self.item

        #for r in item.required: #Redundant !
            #nevt=DeclareEvt(evt.source,evt.actor,r)
            #self.add_sim_child(nevt)

        nevt=DeclareEvt(evt.source,evt.actor,item)
        self.decl=nevt
        self.add_sim_child(nevt,priority=1)
        nevt.parent=self


#        self.signal(evt.type,'change_infos_canvas',evt.item,claimed=evt.actor,evoked=match.turn)
        grp=match.data.actorsubgraphs[self.actor][self.actor]
        self.child_chginfo(item,grp,claimed=evt.actor,priority=-1)
        for act in match.actors:
            actinf=match.cast.get_info(act)
            sub=match.data.actorsubgraphs[act][act]
            for key,eff in actinf.get('effects',{}).iteritems():
                if item ==key[0]:
                    cond=key[1]
                    eff=(cond*match.ruleset.truth_value( sub.get_info(item,'truth')) )*eff[1]
                    self.child_chginfo(act,match.cast.data,effects={(item, cond):('terr',eff)},priority=-1)
        #match.canvas.handler.center_on(evt.item)
        return True


class ConcedeEvt(MatchEvent):
    #Whenever the owner of a node is persuaded to transfer it to someone else
    #(accompanied with large face gain)
    desc ='Concede'


    dft={
        'actor':None,
        'item':None,
        'receiver':None,
        }

    def __init__(self,source,actor,receiver,item,**kwargs):
        super(ConcedeEvt, self).__init__(source,**kwargs)
        self.type='concede_evt'
        self.actor=actor
        self.receiver=receiver
        self.item=item
        self.args=item,
        self._cost=0


    def __str__(self):
        return '{} {} to {} {}'.format(self.desc,self.actor, self.receiver,self.item)

    def prep_do(self,match,*args,**kwargs):
        item=self.item
        iti = match.canvas.get_info(item)
        if  iti['claimed'] !=self.actor.trueID :
            return False
#        acti = match.cast.get_info(self.actor)
        self.effects=match.ruleset.concede_effects(self.actor,self.receiver,iti)
        self.turn = match.turn
        grp=match.data.convgraph
        self.child_chginfo(item,grp,claimed=self.receiver.trueID)
        for act in match.actors:
            actinf=match.cast.get_info(act)
            for key,eff in actinf['effects'].iteritems():
                if item ==key[0]:
                    cond=key[1]
                    eff=(cond*match.ruleset.truth_value( sub.get_info(item,'truth')) )*eff[1]
                    self.child_chginfo(act,match.cast.data,effects={(item, cond):('terr',eff)})
        return True



class JumpEvt(MatchEvent):
    desc ='Jump'
    dft={'actor':None,
        'pos':None}

    def __init__(self,source,**kwargs):
        MatchEvent.__init__(self,source,**kwargs)
        self.type='jump_evt'
        #self.cost =cost
        #self.actor=actor
        #self.pos=kwargs.get('pos',None)


    def __str__(self):
        return '{} {} {}'.format(self.desc,self.actor,self.radius)

    def prep_init(self,match,**kwargs):
        self._affects=(match.canvas.graph,match.data)
        return True

    def prep_uninit(self,match,**kwargs):
        return True

    def prep_do(self,match):
        match.set_barycenter(self.pos,external=True)
        return True


class ExploreEvt(MatchEvent):
    desc ='Explore'
    radius=None
    dft={'actor':None,
        'pos':None}

    def __init__(self,source,actor,cost=MatchRuleset.pondermin,**kwargs):
        MatchEvent.__init__(self,source,**kwargs)
        self.type='explore_evt'
        self.cost =cost
        self.actor=actor
        self.pos=kwargs.get('pos',None)


    def __str__(self):
        return '{} {} {}'.format(self.desc,self.actor,self.radius)

    def prep_init(self,match,**kwargs):
        self._affects=(match.canvas.graph,match.data)
        player=self.actor
        infos=match.cast.get_info(player)
        self.radius=match.ruleset.explore_radius(kwargs.get('cost',self.cost),infos)

        icon=ExplorerBeacon(match.canvas,self)
        if not match.controller[player]=='human':
            #Hide enemy's explorer beacon
            icon.rem_from_group(match.canvas.tools)
        else:
            icon.set_anim('appear',len=ANIM_LEN['med'])
        pos= kwargs.get('pos',self.pos)
        if pos==None:
            pos = match.canvas.handler.mousepos()
        self.fakenode=match.canvas.graph.Node()
        match.canvas.add(self.fakenode,pos=pos,icon=icon)
        return True

    def prep_uninit(self,match,**kwargs):
        match.canvas.remove(self.fakenode)

    def prep_do(self,match):

        player=self.actor
        actinf=match.cast.get_info(player)
        sub=match.data.actorsubgraphs[player][player]
        actg=match.data.actorgraph[player]
        icon=match.canvas.icon[self.fakenode]
        nodes= [ n for n in icon.find_neighbors() if actg.contains(n)]
        links=[l for n in nodes for l in actg.links[n] if not sub.contains(l)  ]
        linkp=[n for l in links for n in l.parents ]
        added=[]
        for n in [n for n in nodes if not n in linkp and not sub.contains(n)]+links :
            if n.type=='node':
                if True in [f.val in ('Exclude','LinkOnly') and f.test_cond(match)
                            for f in actg.get_info(n,'cflags')]:
                    continue
            else:
                if True in [f.val in ('Exclude',) and f.test_cond(match) and not
                        sub.contains(p) for p in n.parents for f in actg.get_info(p,'cflags')]:
                    continue
            if not match.ruleset.discovery_proba(actinf,n,self.cost):
                continue
            #print 'Explore has found',n
            self.child_add(n,sub)
            added.append(n)
            if len(added)>= match.ruleset.discovery_threshold(actinf,self.cost):
                break
        match.canvas.remove(self.fakenode)
        #for l in match.canvas.layers:
            #try:
                #del l.pos[self]
            #except:
                #pass
        #EventHandler.do(self)

        return True

class PathosEvt(MatchEvent):
    desc='Pathos'

    dft={
        'val':None,
        'item':None,
        'cond':None,
        'path_type':None,
        'targets':None,
        }

    def __init__(self,source,actor,item,cond,val,**kwargs):
        MatchEvent.__init__(self,source,**kwargs)
        self.actor=actor #cause of the event
        self.item=item
        self.cond=cond
        self.val=val
        self.type='pathos_evt'
        self.path_type=kwargs.get('type',self.type)
        self.targets=kwargs.get('targets',self.actor)

    def __str__(self):
        return '{} {} {} {} {} {} -- Targets {}'.format(self.desc, self.path_typ,self.actor,self.item, self.cond, self.val, self.targets)


    def prep_do(self,match):
        val=self.val
        tgts=self.targets
        if not hasattr(tgts,'__iter__'):
            tgts=tgts,
        it=self.item
        self.child_chginfo(self.actor,match.cast.data,path=-val,additive=True)

        for act in tgts:
            val2=rfloat(match.ruleset.pathos_effectiveness(self.actor,act)*val)
            actinf=match.cast.get_info(act)
            terf=actinf['terr']-actinf['teri']
            tval=min(terf,val2)
            sub=match.data.actorsubgraphs[act][act]

            if sub.get_info(it,'terr'):
                tval+= sub.get_info(it,'terr')
            self.child_chginfo(it,sub,terr=tval)


            if act!=self.actor:
                sub2=match.data.actorsubgraphs[self.actor][act]
                self.child_chginfo(it,sub2,terr=tval)


            self.child_chginfo(act,match.cast.data,teri=tval)
            eff=(self.cond*match.ruleset.truth_value( sub.get_info(it,'truth')) )*tval

            if actinf['effects'].get((it,self.cond) ,(None,None))[0]=='terr':
                eff+= actinf['effects'][(it,self.cond)][1]

            self.child_chginfo(act,match.cast.data,effects={(it, self.cond):('terr',eff)})

class PolitenessEvt(MatchEvent):
    desc='Politeness'

    dft={
        'val':None,
        'disc_type':None,
        'actor':None
        }

    def __init__(self,source,actor,val,**kwargs):
        MatchEvent.__init__(self,source,**kwargs)
        self.actor=actor
        self.val=val
        self.type='politeness_evt'
        self.disc_type=kwargs.get('type',self.type)
        if 'type' in kwargs:
            self.desc+=self.disc_type

    def prep_init(self,match):
        #ainf=match.cast.get_info(self.actor)
        cons={}
        targets=self.kwargs.get('target',match.actors)[:]
        if not self.actor in targets:
            targets.append(self.actor)
        for act in targets :
            #if act == self.actor:
                #There could be face effects for the rude player
                # maybe predatory, stealing some face at high cost
               # continue
            eff=match.ruleset.politeness_effects(self.disc_type,self.actor,act,self.val)
            for i,j in eff.iteritems():
                cons[(act,i)]=j
            self.effects=cons
        return True

class BatchEvt(MatchEvent):
    desc='Batch'
    #State 1 : The starting event is submitted to gather reactions
    #State 2 : A transcript of the whole batch is made

    dft={
        'root_events':[],
        'actor':None,
        }

    def __init__(self,events=(),*args,**kwargs):
        self.actor=kwargs.pop('actor',None)
        MatchEvent.__init__(self,None,*args,**kwargs)
        self.type='batch_evt'
        self.root_events=[]
        self.child_events={}

        self.events=[]
        for e in events:
            self.add_event(e)

    def __str__(self):
        return '{} {}  -- {}'.format(self.desc,self.actor,self.root_events)


    def duplicate_of(self,evt):
        if not evt.type==self.type:
            return False
        if not False in [True in [s.duplicate_of(s2) for s2 in evt.events ]
                for s in self.events]:
            return True
        return False

    @property
    def rec_events(self):
        #recursive crawl through all the children of events in this batch
        batch_evts=set(self.events[:])
        for e in tuple(batch_evts):
            batch_evts=batch_evts.union( e.all_children(1) )
        return batch_evts

    def add_event(self,evt):
        if evt in self.events:
            return False
        if evt.parent in self.events :
            self.child_events.setdefault(evt.parent,[]).append(evt)
        elif evt.parent and evt.parent.parent in self.events :
            self.child_events.setdefault(evt.parent.parent,[]).append(evt)
        else :
            self.root_events.append(evt)
        for e in self.root_events:
            if e.parent == evt or e.parent and e.parent.parent == evt:
                self.root_events.remove(e)
                self.child_events.setdefault(evt,[]).append(e)
        evt.batch=self
        self.events.append(evt)

    @property
    def cost(self):
        return sum(e.cost for e in self.root_events)


    def add_effect(self,effects,i,j):
        #i is (target,resource), j is value or
        if hasattr(j,'keys'):
            effects.setdefault(i,{})
            for z,k in j.iteritems():
                effects[i].setdefault(z,0)
                effects[i][z]+=k
        else :
            effects.setdefault(i,0)
            effects[i]+=j

    def prep_do(self,match,*args,**kwargs):
        for e in self.rec_events:
            if 'concede' in e.type :
                self.add_event(e)
        match.test_scripts(self) #collect other events added by script
        effects={}
        evact={}
        for evt in self.events:
            if hasattr(evt,'actor'):
                evact.setdefault(evt.actor,[]).append(evt)
        for actor,evts in evact.iteritems():
            for evt in evts:
                if  'decl' in evt.type:
                    info = match.canvas.get_info(evt.item)
                    for e in info.get('effects',()):
                        targets=e.target
                        if targets=='claimer':
                            targets=evt.actor,
                        elif targets=='hearer':
                            targets=tuple(i for i in match.cast.actors if i != evt.actor)
                        elif not hasattr(targets,'__iter__'):
                            targets=targets,
                        val=e.val
                        if e.res=='prox' and not hasattr(val,'keys'):
                            val={self.actor:e.val}
                        for target in targets:
                            if hasattr(val,'keys') and target in val:
                                continue
                            self.add_effect( effects, (target,e.res), val )
                elif hasattr(evt,'effects') and evt.effects:
                    for i,j in evt.effects.iteritems():
                        self.add_effect(effects,i,j)

            #once all effects are compiled, add proximity effects coming from attacks
            for t,val in tuple(effects.iteritems()):
                if t[1] in ('face','terr') and t[0]!= actor and val<0 :
                    eff={actor: match.ruleset.FTA_effect(t[1],val)}
                    self.add_effect(effects,(t[0],'prox'),eff)

        for t,val in tuple(effects.iteritems()):
            #if hasattr(val,'keys'):
                #addi=False
            #else :
                #addi=True
            if not val or hasattr(val,'keys') and not array(val.values()).any() :
                del effects[t]
                continue
            #if t[1]=='prox':
                #self.child_chginfo(t[0],match.cast.data,**{t[1]:{ self.actor,val},'additive':True})
            #else:
            self.child_chginfo(t[0],match.cast.data,**{t[1]:val,'additive':True})
        self.effects=effects


"""
        if 'beacon' in source:
            if 'kill' in sgn:
                evt=sarg[0]
                self.rem_queue(evt)
                self.canvas.remove(signal)

        if 'explore' in sgn:
            if 'start' in sgn:
                self.explore()

            if 'kill' in sgn:
                for evt in self.queue:
                    if sarg[0] in evt.args :
                        self.rem_queue(evt)

            if 'complete' in sgn:
                True

        if 'reveal' in sgn:
            self.canvas.active_graph.add(sarg[0])
            self.canvas.add(sarg[0])
            self.canvas.catch_new()
            self.canvas.assess_itemstate()
            return True

        if 'public' in sgn:
            for actor in self.actors:
                self.data.actorgraph[actor].add(sarg[0])
"""
