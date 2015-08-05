# -*- coding: utf-8 -*-

from gam_import import *


class LogicRuleset():
    def __init__(self,data):
        self.data=data

    def truth_value(self,truth):
        if truth <1./3:
            return -1
        elif truth >2./3:
            return 1
        return 0

    def truth_disagreement(self,truth1,truth2):
        if self.truth_value(truth1)!=self.truth_value(truth2) :
            return True
        return False

    def link_effect_from_source(self,st,logic):
        #depending on source truth, effect on target
        st=self.truth_value(st)
        if st==2*logic[0]-1:
            return 2*logic[1]-1
        if logic[2] and st==1-2*logic[0]:
            return 0
        return None
    def link_effect_from_target(self,tt,logic):
        #depending on source truth, effect on target
        tt=self.truth_value(tt)
        if logic[3] and tt==1-2*logic[1]:
            return 0
        return None

    def calc_truth(self,node,graph,sub,**kwargs):
        #Truth of a node during the conversation, including link contributions
        #graph is mindscape of the observer, sub is what he thinks is true for
        #the mindscape he is computing truth in (could be his own, could be someone else's)
        base= kwargs.get('bias',sub.get_info(node,'bias'))+.5
        case='typ'
        extrapolate=kwargs.get('extrapolate',0)
        if extrapolate:
            #case where the observer assumes that his own links are all known to the other
            #(this is useful in Reac to compute perceived bias, i.e. how much the other seems prejudiced)
            links=[l for l in graph.links.get(node,[]) if sub.contains(
                l.parents[1-l.parents.index(node)])]
            links+= sub.links.get(node,[]) #this is necessary in case sub contains new links (learned from outside)
        else:
            #case where the observer computes only from links he knows that the other knows
            links = sub.links.get(node,[])
        links=set(links)
        if 'exclude_links' in kwargs:
            for l in kwargs['exclude_links']:
                if l in links:
                    links.remove(l)
        for l in links:
            logic=graph.get_info(l,'logic')
            magn=sub.get_info(l,'val')
            if node==l.parents[1]:
                st= sub.get_info(l.parents[0],'truth')
                if logic[0]==round(1+self.truth_value(st))/2:
                    if logic[1]==1:
                        base+=magn
                        case='normal+'
                    else :
                        base-=magn
                        case='normal-'
                elif logic[2]:
                    if logic[1]==1:
                        if base>.5:
                            base=max(.5,base-magn/2.)
                        case='doubt-'
                    else :
                        if base <.5:
                            base=min(.5,base+magn/2.)
                        case='doubt+'
            if node ==l.parents[0] and logic[3]:
                st= sub.get_info(l.parents[1],'truth')
                if logic[1]!=int(round(.5+.5*self.truth_value(st))):
                    if logic[0]==1:
                        if base>.5:
                            base=max(.5,base-magn/2.)
                        case='reverse-'
                    else :
                        if base <.5:
                            base=min(.5,base+magn/2.)
                        case='reverse+'
            if 0:
                try:
                    print '===',sub, st, 'logic:', logic,'case',case,'truthsource', round(1+self.truth_value(st))/2
                except:
                    print '===', sub, 'nost'

        #print 'truthcalc',sub.get_info(node,'name'),graph.get_info(node,'truth'),'to', base# graph, sub, node
        return max(0,min(base,1))


class MatchRuleset(LogicRuleset):
    pondermin=.3
    speechactmin=.3

    @property
    def match(self):
        return self.data

    @property
    def cast(self):
        return self.match.cast
    @property
    def graph(self):
        return self.match.graph
    @property
    def setting(self):
        return self.match.setting

    def init_prox(self,act1,act2):
        '''Compute starting match proximity of act1 to act2 from their info sets,
        taking into account their base prox value and the setting.'''
        ainf=self.cast.get_info(act1)
        oinf = self.cast.get_info(act2)
        base=ainf['prox'][act2.trueID]
        setting =self.setting
        return base


#Match setting creation

    def actor_should_know(self,actor,item):
#        print item,
        iti= self.graph.get_info(item)
        act=self.cast.get_info(actor)
        threshold=act['subt']
        if item.type=='node':
            for talent in act['prof']:
                threshold +=getattr(talent,iti['genre'])
        if iti['subt']<threshold:
            return True
        else :
            return False

#Match initialization: Actor subgraphs

    def actor_selfgraph_init_rule(self,actor,item):
        # Should an item belong to the initial actor graph ?
        iti= self.match.actorgraph[actor].get_info(item)
        act=self.cast.get_info(actor)
        if 'cflags' in iti:
            if True in [i in iti['cflags'] for i in ('Include','Starter','Doxa')]:
                return True
            if 'Random' in iti['cflags']:
                #Random case:
                val = iti['val']
                prof = act['prof']

                return rnd.uniform(0,1)>.5
        return False

    def actor_othergraph_init_rule(self,actor,other,item):
        # Should an item belong to the initial other graph ?
        iti= self.match.actorgraph[actor].get_info(item)
        oti= self.match.actorgraph[other].get_info(item)
        act=self.cast.get_info(actor)
        oth=self.cast.get_info(other)
        if 'cflags' in iti:
            if 'Doxa' in iti['cflags']:
                return True
            if 'Perceived' in iti['cflags']:
                return {'truth':self.perceive_info(oti['truth'],act)}
        return False

# Time and relationships


    def time_allowance(self,actor):
        actors=self.match.cast.actors
        tot=len(actors)
        totface=sum(self.match.cast.get_info(a,'face') for a in actors)
        return float(tot)/totface

    def explore_radius(self,cost,infos):
        typ=ergonomy['canvas_typical_dist']/hypot(*ergonomy['default_canvas_size'])
        rad= max(typ/2., min(sqrt(cost*infos['agil'])*typ*4, 4.*typ ))
        #print 'explore radius', rad, 'min max',typ/2., typ*4.
        return rad

    def politeness_effects(self,typ,*args,**kwargs):
        src_actor=args[0]
        srcinf=self.cast.get_info(src_actor)
        tgt_actor=args[1]
        src=src_actor.trueID
        tgt=tgt_actor.trueID
        tgtinf=self.cast.get_info(tgt_actor)
        val=args[2]
        if typ == 'overtime' and src!=tgt:
            val*=0.05
            val=round(val*database['floatprecision'])/float(database['floatprecision'])
            prox ={}
            prox.update(tgtinf['prox'])
            prox[src]=val
            return {'prox':prox}

        res1,res2=0,0
        if typ=='apology':
            'Apology (F-F)'
            res1,res2='face','face'
        if typ=='compliment':
            'Compliment (F-T)'
            res1,res2='face','terr'
        if typ=='deference':
            'Deference (T-F)'
            res1,res2='terr','face'
        if typ=='promise':
            'Promise (T-T)'
            res1,res2='terr','terr'
        if typ=='criticism':
            'Criticism (F)'
            res2='face'
        if typ=='doubt':
            'Doubt (T)'
            res2='terr'
        if res1 and res2:
            val=rfloat(val*0.1)
            if tgt==src:
                return {res1:-val}
            fact=(1+tgtinf['prox'][src] )/2. #goes from 50% to 100% effectivity
            return {res2:rfloat(fact* val),'prox': {src: rfloat(val/4)}}
        elif res2:
            val*=0.05
            if tgt==src:
                return {}
            fact=2./(1+tgtinf['prox'][src] ) #goes from 50% to 100% effectivity
            return {res2:- rfloat(fact*val)}
        return {}

    def concede_effects(self,giver,receiver,iteminfo):
        effects={}
        effects[(receiver,'prox')]={giver.trueID:+0.05}
        magn=iteminfo['val']
        effects[(receiver,'face')]=rfloat(0.1*magn)
        return effects

    def FTA_effect(self,typ,val):
        if val>=0:
            return 0
        if typ=='face':
            val*=.4
        elif typ=='terr':
            val*=.2
        else:
            val=0
        return rfloat(val)

    def conv_radius(self,actor):
        #This radius is how much other actors will allow the current one to
        #stray away from the barycenter of the conversation
        #and therefore increases with proximity.
        totprox=0
        nbact=0
        for act in self.cast.actors :
            if act!=actor:
                totprox+= self.cast.get_info(act,'prox')[actor.trueID]
                nbact+=1
        dist=ergonomy['canvas_typical_dist']
        if not nbact:
            return database['conv_radius_mult']*dist

        return max(dist,database['conv_radius_mult']*dist*sqrt(totprox/float(nbact)))

# Actions


    def claim_together(self,item,match,**kwargs):
        '''Rules for which items should automatically be claimed together
        with item. Possible choices include:
            - links together with node
                - all of them
                - only those that agree, else none
                - preferably those that agree
                - the last mentioned'''

        option=kwargs.get('option',
            ['none','all','only_agree','pref_agree','last'][1])
        if option=='none':
            return []
        canvas=match.canvas
        prev_cand=kwargs.get('prev_cand', set())  #for recursive cases
        cand=[]
        if item.type=='node':
            for l in canvas.active_graph.links[item]:
                oth=[n for n in l.parents if n!= item][0]
                if canvas.get_info(oth,'claimed'):
                    cand.append(l)

            if 'agree' in option:
                itruth=canvas.get_info(item,'truth')
                agree=[l for l in cand if l.type=='link' and
                        self.logic.link_effect_from_target(itruth,
                            canvas.get_info(l,'logic')) ]
                if 'only' in option or agree:
                    cand=agree
        if option=='last':
            #Last candidate only
            if len(cand)>1:
                cand=sorted(cand,key=lambda e:canvas.get_info(e,'lastmention'))[-1:]
        #Recursive
        cand=set(cand)
        if cand==prev_cand:
            return cand
        kwargs['prev_cand']=cand
        cand=set([z for c in cand if c!=item for z in self.claim_together(item,match,**kwargs) ])
        return prev_cand.union(cand)

    def claim_cost(self,item,item_infos,actor_infos):
        #Speech time cost for a claim
        if item.type=='node':
            return item_infos['val']/(1.+actor_infos['agil'])
        if item.type=='link':
            return .2
        return 0

    def discovery_proba(self,act,item,length=.3):
        iti= self.graph.get_info(item)
        threshold=act['subt']
        if item.type=='node':
            for talent in act['prof']:
                threshold +=getattr(talent,iti['genre'])
        if iti['subt']>threshold:
            return False
        if rnd.random()<act['agil']/iti['subt']*length:
            return True
        else :
            return False

    def discovery_threshold(self,act,length=.3):
        #max number of discoveries
        return max(1,4*act['agil']*length)



    def perceive_truth(self,baseval,ainf):
        extr=self.truth_value(baseval)/6.+.5 #This gives the boundary for keeping same truthvalue
        diff=extr-baseval #This is how much the real truth exceeds the boundary
        #If the random number is 1 exactly, the opinion is brought back to boundary
        #If it is negative, the opinion is over-intensified
        return max(0,min(1,baseval+diff*(1-ainf['perc'])*rnd.uniform(-1,1)))

    def accept_truth(self,baseval,actor,oinf):
        prox = oinf['prox'][actor.trueID]
        agreement=int(round(prox*3 -1))
        effects=[]
        return 0.5 + (baseval-0.5)*prox, effects,agreement


    def contrast_truth(self,received_truth,believed_truth):
        test1=int(received_truth*3)
        test2=int(believed_truth*3)
        if abs(test1-test2) >1 :
            agreement= -1
        elif abs(test1-test2) ==1 :
            agreement = 0
        else:
            agreement = +1
        effects={}#'prox':agreement * .05}
        #TODO: think about agreement effects later
        return effects, agreement

    def perceive_info(self,info,ainf):
        rd= rnd.uniform(-1,1)*(1-ainf['perc'])/2.
        return max(0,min(info + rd,1))


    def concede_test(self,giver,receiver,iteminfo,preval,newval):
        giverinfo = self.cast.get_info(giver)
        receivinfo=self.cast.get_info(receiver)
        dif=newval-preval
        if dif>0:
            thresh=2./3.
        else:
            thresh=1./3.
        scaledif= dif/ (thresh-preval)
        if scaledif <0:
            return False
        if scaledif>1: #logically, should be convinced
            scaledif=1+scaledif

        dethos=receivinfo['face']-giverinfo['face']+giverinfo['prox'][receiver]
        terr=giverinfo['terr']
        magn=iteminfo['val']
        investerr,investdir=iteminfo.get('terr',(0,1) )

        proba = scaledif*(1.+dethos)*(1 +copysign(investerr/terr, (investdir-0.5)*dif))*(1-magn/10)
        return rnd.random()<proba

    def pathos_effectiveness(self,actor,target):

        if actor==target:
            return 1.
        actinf=self.cast.get_info(actor)
        tgtinf=self.cast.get_info(target)
        prox=tgtinf['prox'][actor]
        return .5*(prox)*(2-tgtinf['terr'])



# OLD OBSOLETE



    def is_doxic(self,item):
        #OBSOLETE : doxa is just high val, low subtlety
        info= self.graph.get_info(item)
        if item.type=='link':
            if info['pattern']=='Doxic':
                return True
            return False

        if info['val'] > 1.2:
            return True
        return False