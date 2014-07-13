# -*- coding: utf-8 -*-

#WIP: AI for NPC

from gam_match_script import *
from gam_match_events import *

class AIPlayer(object):

    personality=['cooperative','aggressive'][0]

    #tactical objectives
    objectives={
        'claim node':2,
        'claim link':3,
        'link proof':4, #link whose logical consequence is good for my beliefs
        'link disproof':-1, # '' bad for my beliefs
        'node per link':.5, #when claiming node, how much links proof/disproof count
        'self loss':-5,
        'self gain':4,
        'other loss':-2,
        'other gain':-1,
        'explore':1
        }
    #each objective furthermore has modifiers (intensities and so on)
    modifiers={
        'self loss':{'val':lambda e:20*e }
        }

    #strategic goals
    goals={

        }

    # Hotness of each node, computed through a combination of betwenness centrality
    hotness={}

    def __init__(self,actor,match,**kwargs):
        self.actor=actor
        self.match=match
        self.rule=match.ruleset
        self.graph=match.data.actorsubgraphs[actor][actor]
        self.ographs={act:match.data.actorsubgraphs[actor][act] for act in match.actors if act!=actor}
        self.queue=[]
        self.done=[]

    def make_objectives(self):
        #depending on personality, change value of objectives
        self.objectives

    def eval_node(self,node,links):
        obj=self.objectives
        actor=self.actor
        match=self.match
        graph=self.graph

        value =obj['claim node']
        effects=graph.get_info(node,'effects')
        for eff in effects:
            tgt=eff.target
            val=eff.val
            txt=''
            if tgt==actor:
                txt+='self '
            else :
                txt+='other '
            if val >0:
                txt +='gain'
            else:
                txt +='loss'
            value += obj[txt]*(abs(val)*20)
        for l in links[node]:
            value += self.eval_link(l)- obj['claim link']
        return value

    def eval_link(self,link):
        obj=self.objectives
        actor=self.actor
        match=self.match
        graph=self.graph

        value =obj['claim link']
        pinfos=[graph.get_info(p) for p in link.parents]
        sinfos=graph.get_info(link)
        try:
            ptruth=[.5*(1+ self.rule.truth_value(i['truth']) ) for i in pinfos]
        except:
            print pinfos
            return 0

        if ptruth[0] == sinfos['logic'][0]:
            if ptruth[1] == sinfos['logic'][1]:
                value +=obj['link proof']
            if ptruth[0] == 1- sinfos['logic'][0]:
                value +=obj['link disproof']


        return value

    def accessible(self,prev=[]):
        #TODO: use the mask instead
        match=self.match
        actor=self.actor
        graph=self.graph

#        mask=match.canvas.handler.fog.mask
        #mask.invert()
        #icons=match.canvas.
        #mask.invert()
        #nodes = [i.item for i in icons]
        bary,rad=match.data.active_region
        nodes=[i for i in graph.nodes if not i in prev and hypot(*array(match.canvas.graph.pos[i])-bary)/rad <1.]
        links=graph.links

        nunclaimed,lunclaimed=[],[]
        for i in nodes :
                if not graph.get_info(i,'claimed'):
                    nunclaimed.append(i)
                for l in links[i]:
                    if l not in lunclaimed and not graph.get_info(l,'claimed') :
                        lunclaimed.append(l)

        return set(nunclaimed), set(lunclaimed)

    def make_turn(self):
        match=self.match
        obj=self.objectives
        actor=self.actor
        graph=match.data.actorsubgraphs[actor][actor]
        nodes=graph.nodes
        links=graph.links
        batch=None
        #print actor, 'knows node', nodes,'and can claim', unclaimed
        if not nodes:
            print 'player has nothing to do!'
            return match.add_phase(FuncWrapper(match.next_player))
        #nunclaimed,lunclaimed = self.accessible()
        #values={}
        #for node in nunclaimed:
            #values[node] =self.eval_node(node,links)
        #for link in lunclaimed:
            #values[link] =self.eval_link(link)

        for q in tuple(self.queue):
            try:
                q()
            except:
                self.queue.append(lambda e=q: user.evt.do(q,2))
            self.queue.remove(q)

        while match.time_left-match.time_cost >0:
            nunclaimed,lunclaimed=match.available_claims(actor,0)
            print actor, nunclaimed,lunclaimed
            if database['demo_mode']:
                nunclaimed=[]
            values={}
            for node in nunclaimed:
                values[node] =self.eval_node(node,links)
            for link in lunclaimed:
                values[link] =self.eval_link(link)
                #for p in link.parents:
                    #if p in nunclaimed and not p in newn:
                        #values[p]=self.eval_node(p,links)

            best=sorted(values.items(),key=lambda e:e[1])
            if best:
                bestitem,bestvalue=best[-1]

            if not best or obj['explore']>bestvalue :
                if  database['demo_mode']:
                    #match.add_phase(FuncWrapper(match.next_player))
                    break
                else:
                    item = rnd.choice(nodes)
                    cst=max(0.3,match.time_left-match.time_cost)
                    nevt = ExploreEvt('AI', actor,pos=match.canvas.graph.pos[item],cost=cst)
                    cevt=QueueEvt(nevt,match.data,newbatch=True)
                    user.evt.do(cevt,1)
                #break
            else :
                print 'best item', bestitem, bestvalue
                nevt = ClaimEvt('AI', actor,bestitem)
                cevt=QueueEvt(nevt,match.data,newbatch=True)
                user.evt.do(cevt,1)
                if bestitem.type=='node':
                    nunclaimed.remove(bestitem)
                else:
                    lunclaimed.remove(bestitem)
                del values[bestitem]
                #print match.time_cost,match.time_left

                #self.queue.append(lambda:user.ui.match.canvas.handler.center_on(bestitem))

            #nunclaimed|=newn
            #lunclaimed|=newl

            #de-ident the following to have all actions in one batch
            batch=cevt.batch
            #print 'adding phase', batch, id(batch), cevt
            #print 'to', match.phase_queue
            self.queue.append(lambda b=batch:user.evt.do(b,2))
        match.add_phase(FuncWrapper(self.next_action) )
            #match.next_phase()
        match.advance_phase()
        #match.next_player()
        #match.next_player()
        #user.evt.do(batch,2)

    def next_action(self):
        #print 'NEXT ACTION==================================', self.queue
        match=self.match
        if self.queue:
            act=self.queue.pop(0)
            self.done.append(act())
        if self.queue:
            match.add_phase(FuncWrapper(self.next_action))
        else:
            match.add_phase(FuncWrapper(self.test_finish))


    def test_finish(self):
        match=self.match
        n,l=match.available_claims(self.actor,0)
        new=0
        if  match.time_left:
            new=1
            try:
                if match.time_left == self.last_test:
                    new=0
            except:
                pass
        if new:
            self.last_test=  match.time_left
            #in case actions have unlocked new possibilities
            return self.make_turn()
        else:
            match.available_claims(self.actor,1)
        if not self.done:
            match.add_phase(FuncWrapper(lambda:match.call_scripts('noact_'+self.actor.name)) )
        self.done=[]
        match.add_phase(FuncWrapper(match.next_player))