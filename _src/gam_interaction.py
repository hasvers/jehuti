# -*- coding: utf-8 -*-


## Interaction Model

#When a player makes a decisive action (claim, dispute...)
#this model computes reactions and interpretations


#Depending on the strength of (dis)agreement, ease of its perception increases:
    # - stays impassible
    # - seems skeptical
    # - nods approvingly
    # - smiles
#More demonstrative characters have a multiplier to the strength of their agreement
#(if reaction is voiced, then perception is fully accurate.)
#Probability of demonstration depends on proximity, face and territory of characters
#(and some personality trait?)


#WHat happens if one speaker creates a bias in a listener by stating a truth level
#that is accepted by the other, then the first reveals the links that cause his own truth value?
#should those links increase the truth value for the listener even further?
#(thus making the listener more convinced than the speaker?)
#Could be plausible: if the speaker has created a bias in the listener, it's through
#irrational means (ethos or proximity). A purely rational listener would not have had
#the bias before hearing the links and agreeing to them.


from gam_script import *
from gam_canvas_events import TruthCalcEvt,ReactLinkDiscoveryEvt

#### GAME RULES #####===========================================================
#Attempt to separate game logic from basic engine pocesses


class PsychologyModel(object):
    '''Model of the psychology of any character. Useful both for
    interaction (i.e. reactions and interpretations) and for
    AI planning.

    If necessary, I will later add personality traits to characters
    (Possibly a simple bidimensional Jung-like vector)'''

    def __init__(self,ego):
        self.ego=ego

    def eagerness(self,actor,infosrc):
        '''Eagerness to please actor, rescaled in [0,1].
        Depends on the difference between prox[ego][actor] and prox[actor][ego].'''
        ego=self.ego
        if world.get_object(ego) == world.get_object(actor):
            raise Exception("Self eagerness!")
        eag=infosrc.get_info(ego,'prox')[actor]- infosrc.get_info(actor,'prox')[ego]
        return (eag+1.)/2

    def difface(self,actor,infosrc):
        '''Face difference (ego-actor), rescaled in [0,1]'''
        ego=self.ego
        dif=infosrc.get_info(ego,'face')- infosrc.get_info(actor,'face')
        return (dif+1)/2.

    def demonstrativeness(self,actor,infosrc):
        '''How likely ego is likely to speak their mind to actor.'''
        eagerness=self.eagerness(actor,infosrc)
        confidence=self.difface(actor,infosrc)
        return eagerness+confidence

    def emotion(self,factors,infosrc):
        '''Compute the emotion resulting from a series of factors.
        Emotion is a complex variable, with abs(emo) the intensity
        and arg(emo) the hue.
        Russel and Barret model of core affect:
            Re: pleasantness
            Im: activation'''
        emo=0+0J
        pleas=0 #How pleasant the experience is
        active=0 #How busy the experience is
        for e in factors:
            if e.type=='ethos':
                pleas+=self.ethos_positivity(e.effects)
            elif e.type=='opinion_divergence':
                pleas-=.5
                active+=1.
            elif e.type=='concede':
                pleas-=1.
                active+=1.
            elif e.type=='opinion_shift':
                active+=1.
            elif e.type=='deep_shift':
                active+=3.
            elif e.type=='unknown_pattern':
                pleas-=1.
                active+2.
            elif e.type=='teri_change':
                active+=1.
            elif e.type=='teri_activ':
                #if invested territory gets activated/lost,
                #huge emotional impact
                please+=3*e.val
        ethos=self.ethos_positivity(self.ethos_effects(factors))
        pleas+=ethos
        active+=abs(ethos)

        emo=pleas/5.+1J*active/8.
        return emo

    def ethos_effects(self,factors):
        '''Compute the ethos effects resulting from various factors.'''
        face,terr,prox=0,0,0
        eps=0.05 #Standard increment
        for e in factors:
            if e.type=='discovery':
                pass
                #if e.agreed:
                    #face
            elif e.type=='opinion_divergence':
                prox-= eps
            elif e.type=='concede':
                #match.ruleset.concede_effects
                face-= 2*eps
            elif e.type=='opinion_shift':
                terr-=eps
            elif e.type=='deep_shift':
                terr-= 3*eps
            elif e.type=='unknown_pattern':
                face-= eps
            elif e.type=='reeval_bias':
                #If the actor seems less biased, like them more
                prox+= eps* abs(e.val)
        ethos= {'face':face,'terr':terr,'prox':prox}
        return {i:j for i,j in ethos.iteritems() if j!=0}

    def ethos_positivity(self,dico):
        '''Takes a dictionary of ethos effect and returns how
        positive the summed outcome is taken to be.'''
        return dico.get('face',0)+dico.get('terr',0)+dico.get('prox',0)/2.

    def perceive_bias(self,actor,match):
        '''How biased ego perceives actor to be in their opinions.
        Could intervene in trust and proximity. '''
        bias=0
        graph=match.data.actorsubgraphs[self.ego][actor]
        if not graph.nodes:
            return bias
        for n in graph.nodes:
            bias+=abs(graph.get_info(n,'bias'))
        bias/=len(graph.nodes)
        if len(graph.nodes)<8:
            #Too little data to judge bias comfortably
            bias*=len(graph.nodes)/8.
        return bias

    def perceive_trait(self,trait,actor,infosrc):
        '''For all psychological traits, how well does ego evaluate them
        in actor? This is a fight between ego.perc and act.terr'''
        #Converges to trait (perc wins) or to 0 (terr wins)
        egoinfos=infosrc.get_info(self.ego)
        actinfos=infosrc.get_info(actor)
        perc=egoinfos['perc']
        if not perc:
            perc=.05
        terr=actinfos['terr']
        #print perc,terr,exp(-terr/4./perc)
        return trait*exp(-terr**2/2./perc)

    def trust_opinon(self,actor,match):
        '''How likely ego is likely to trust actor's opinion
        irrationally, and thus become biased. Depends on actor's
        authority, on ego's' prox to actor, on ego's eagerness
        to please, and on how biased ego believes actor to be in general.
        '''
        ego=self.ego
        infosrc=match.cast
        prox=infosrc.get_info(ego,'prox')[actor]
        eagerness=self.eagerness(actor,infosrc)
        authority=infosrc.get_info(actor,'face')
        bias = self.perceive_bias(actor,match)
        return authority/2.+(prox+eagerness)/4


    def pathos_effectiveness(self,ego,actor):
        #IMPORTANT: reverse order of arguments compared to gam_rules
        '''How effective is an appeal to pathos on ego by actor.
        Increase with proximity to actor, decreases with ego's territory.'''
        ego=self.ego
        if actor==ego:
            return 1.
        egoinf=self.cast.get_info(ego)
        actorinf=self.cast.get_info(actor)
        prox=egoinf['prox'][actor]
        return .5*(prox)*(2-actorinf['terr'])



class InteractionRules(object):

    update_true_beliefs=1 #Does the truth in the Actorgraph change as a result of conversation?
        #If no, then when nodes are remembered, their truth does not take into account
        #what has transpired since the beginning of the conversation. This is not a
        #problem in most cases snice any link claim to them will trigger a TruthCalcEvt
        #but still.

    factors=(
            #Ego-centered
            'discovery',
            'opinion_shift','deep_shift', #deep_shift=change in doxa/deep belief'concede',
            'unknown_pattern','concede',
            #Alter-centered
           'opinion_divergence','reeval_bias',
            #Pathos and ethos
            'ethos','teri_activ','teri_change'
            )

    def __init__(self, match):
        self.match=match
        self.actors=match.actors
        self.psy={a:PsychologyModel(a) for a in self.actors}

    def verbalisation(self,agreement,emotion):
        '''Threshold for a verbal response that leaves
        no ambiguity on the degree of agreement or emotion.'''
        if abs(agreement)>.8 and abs(agreement)>abs(emotion):
            return 'agreement'
        if abs(emotion)>.8 and abs(agreement)<abs(emotion):
            return 'emotion'
        return None

    #NODE CLAIM AND AGREEMENT

    def belief_creation_under_influence(self,ego,perceived_claim):
        '''Wanting to believe/disbelieve the perceived claim depending on
        ethos and proximity)'''
        trust=self.psy[ego].trust_opinon(perceived_claim.actor,self.match)
        dbias=trust*(perceived_claim.truth-.5)
        if trust>=.5:
            return {'bias': dbias,'truth':.5+dbias}
        else:
            return {}

    def belief_revision_under_influence(self,ego,perceived_claim,infosrc):
        '''Some influence from claimant who can distort remembrance'''
        trust=self.psy[ego].trust_opinon(perceived_claim.actor,self.match)
        infos=infosrc.get_info(perceived_claim.item)
        dbias=trust*(perceived_claim.truth-infos['truth'])/3.
        if trust>.5:
            return {'bias':infos['bias']+ dbias,'truth':infos['truth']+dbias}
        else:
            return {}

    def agreement(self,ego,perceived_claim,infosrc):
        '''Three components to agreement on node:
        opinion difference, was the node just discovered,
        and demonstrativeness.'''
        match=self.match
        actor=perceived_claim.actor
        egotruth=infosrc.get_info(perceived_claim.item,'truth')
        if egotruth is None:
            egotruth=perceived_claim.egoinfos['truth']
        claimtruth=perceived_claim.truth
        agreement= (egotruth+claimtruth-1)**2-(egotruth-claimtruth)**2
        #agreement*=1-.9*perceived_claim.discovery
        agreement*=self.psy[ego].demonstrativeness(actor,match.cast)
        return agreement


    def truth_from_agreement(self,ego,perceived_reac,infosrc):
        '''Make assumption on someone else's opinion based on perceived agreement.
        Inverse of previous function.'''
        egotruth=infosrc.get_info(perceived_reac.item,'truth')
        agr=perceived_reac.agreement
        actor=perceived_reac.actor
        demonstr=self.psy[actor].demonstrativeness(ego,self.match.cast)
        agr/=self.psy[ego].perceive_trait(demonstr,actor,self.match.cast)
        t= (1-agr-2*egotruth)/2
        if t>0 and abs(egotruth-.5)>0.000001:
            t/=(1-2*egotruth)
        return t


    #LINK CLAIM AND AGREEMENT

    def link_discovery(self,ego,perceived_claim):
        if perceived_claim.pattern in self.match.cast.get_info(ego,'patterns'):
            return {}
        else:
            return {'pattern':'Unknown'}

    def agree_inference(self,ego,perceived_claim):
        '''Inferences are automatically accepted if the pattern is
        known, else only if trust is above a threshold.'''
        threshold=.7

        if perceived_claim.pattern in self.match.cast.get_info(ego,'patterns'):
            return 1
        trust=self.psy[ego].trust_opinon(perceived_claim.actor,self.match)
        if trust>threshold:
            return min(1., trust-threshold)
        return 0

    def emotion(self,ego,factors):
        return self.psy[ego].emotion(factors,self.match)

    def interpret_truth_change(self,ego,diftruth,infos):
        '''Is a difference in truth value sufficient to be a change of opinion?'''
        if self.match.ruleset.truth_value(infos['truth']
                )==self.match.ruleset.truth_value(infos['truth']+diftruth):
            return False #Nothing signifcant

        if 'Doxa' in [cf.genre for cf in infos.get('cflags',[])] or abs(
                infos['bias'])>.5:
            return 'deep_shift'
        return 'opinion_shift'

    #Perception stuff

    def perceived_truth(self,ego,claim,infosrc):
        '''When ego receives a claim with a given truthvalue,
        how much error is there on it in the perceived_claim?'''
        baseval=claim.truth
        #return baseval #perfect percepton
        percep=infosrc.get_info(ego,'perc')
        chance=rnd.uniform(-1,1)
        #If chance>0, perceived truth tends toward boundary of ?ness
        #else it is amplified
        extr=rint(2*baseval-1)/6.+.5
        diff=extr-baseval
        return max(0,min(1,baseval+diff*(1-percep)*chance))

    def perceived_agreement(self,ego,reac):
        '''When ego receives a reac with a given agreement,
        how much error is there on it in the perceived_reac?'''
        #The perceived agreement is a function that tends to
        #the real agreement for large values of it
        #but is muddled in the middle
        baseval=reac.agreement
        perc=self.match.cast.get_info(ego,'perc')
        chance=rnd.uniform(-1,1)
        return baseval*(1.+(1-perc)*chance*(1-min(abs(baseval),1)) )

    def perceived_emotion(self,ego,reac):
        '''When ego receives a reac with a given emotion,
        how much error is there on it in the perceived_reac?'''
        #The perceived agreement is a function that tends to
        #the real agreement for large values of it
        #but is muddled in the middle
        baseval=reac.emotion
        perc=self.match.cast.get_info(ego,'perc')
        chance=rnd.uniform(-1,1)
        return baseval*(1.+(1-perc)*chance*(1-min(abs(baseval),1)) )

    def perceived_discovery(self,ego,reac):
        '''When ego receives a reac, do they detect whether
        this was a discovery?'''
        perc=self.match.cast.get_info(ego,'perc')
        if reac.discovery:
            if rnd.uniform(0,1) < perc:
                return 1
        return 0


    def discern_nonverbal(self,ego,nonverbal):
        '''When ego receives a complex nonverbal response, how well
        can they discern the details. With lack of perception, this
        just regresses toward the average value.'''
        nv=nonverbal
        #Average
        aagree,aemote=sum(nv[i][0] for i in nv), sum(nv[i][1] for i in nv)
        mean=(aagree+aemote.real)/2.

        perc=self.match.cast.get_info(ego,'perc')
        #Distinction between agreement and emotion:
        pagree=mean +(aagree-mean)*perc
        pemote=mean+aemote.imag +(aemote.real-mean)*perc
        #
        return {r:(pagree+(nv[r][0]-pagree)*perc**2,
                pemote+(nv[r][0]-pemote)*perc**2 ) for r in nv},(pagree,pemote)



#### MECHANICS #####=============================================================

class InteractionScript(Script):



    def __init__(self,inter,**kwargs):
        Script. __init__(self,**kwargs)
        self.by_actor=DataDict()
        self.interaction=inter

    def parse_interaction(self,scene):
        '''Takes an interaction schema and parses it into a script.'''
        inter=self.interaction
        factors=inter.factors
        events=inter.events
        schema=inter.schema
        ethos=inter.ethos
        roots=[n for n,d in schema.in_degree().items() if d==0]
        states={}
        cur=set(roots)
        state=1
        #With each state is associated a list of interaction stages
        while cur:
            states[state]=[]
            for c in tuple(cur):
                states[state].append(c)
                cur=cur.union(set(schema.successors(c)))
                cur.remove(c)
            state+=1
        calls=[]
        autotext={}
        #For each state, look at the stages associated with that states
        #then look at the factors associated with those stages
        #and see if they fulfill conditions for scripts, that should thus
        #be called by this one.
        for i in states:
            evtcontainer=SceneScriptEffect()
            evtcontainer.typ='container'
            evtcontainer.target=[]
            src=[]
            effects=[evtcontainer]
            autotext[i]=[]
            for s in states[i]:
                src.append(s)
                fac=factors[s]
                src+=fac
                if s.type in ('claim','reac'):
                    handled=None
                    infos=scene.canvas.get_info(s.item)
                    for called in infos['scripts']:
                        #Node/Link scripts
                        if not called.event_check(s.type,s.item,scene):
                            continue
                        if called in calls:
                            continue
                        eff=SceneScriptEffect()
                        eff.typ='Call'
                        eff.target=called
                        effects.append(eff)
                        if hasattr(called,'text') and called.text and s.type=='claim':
                            autotext[i].append((s,called.text))
                            handled=True
                    if not handled and s.type=='claim' and s.item.type=='node':
                        if infos.get('desc'):
                            autotext[i].append((s,infos['desc']))
                        else:
                            autotext[i].append((s,infos['name']))
            self.treat_autotext(autotext[i],effects)
            for s in src:
                for e in events.get(s,()):
                    evtcontainer.target.append(e)
                if not s in ethos:
                    continue
                eth=self.total_ethos_effect(ethos[s])
                for act, infos in eth.iteritems():
                    eff=SceneScriptEffect()
                    eff.typ='Cast'
                    eff.evt='info'
                    eff.target=act
                    eff.info= infos
                    eff.info["additive"]=True
                    effects.append(eff)
            for e in effects:
                self.effects.append(e)

    def treat_autotext(self,autotext,effects):
        for src,txt in autotext:
            #TODO: proper autotext treatment
            teff=SceneScriptEffect()
            teff.typ='Text'
            teff.text=txt
            teff.actor=src.ego
            teff.display='On'
            effects.append(teff)


    def total_ethos_effect(self,eth):
        ego={}
        for e in eth:
            for tup, val in e.iteritems():
                act,typ=tup
                if not act in ego:
                    ego[act]={}
                if not typ in ego:
                    ego[act][typ]=val
                else:
                    if hasattr(val,'keys'):
                        for i,j in val.iteritems():
                            if i in ego[act][typ]:
                                ego[act][typ][i]+=j
                            else:
                                ego[act][typ][i]=j
                    else:
                        ego[act][typ]+=val
        return ego


class Interaction(object):
    '''This is a report on the interaction. All the building is done
    in the InteractionModel, then the Interaction item is created.
    It is parsed to create an InteractionScript that contains all the
    effects (text, ethos effects) as well as the calls to other scripts.'''

    class Stage(object):
        def __init__(self,typ,**kwargs):
            self.type=typ
            for i,j in kwargs.iteritems():
                setattr(self,i,j)

        def __repr__(self):
            info=''
            if 'claim' in self.type:
                if self.item.type=='link':
                    info=self.pattern
                else:
                    info=self.truth
            if 'reac' in self.type:
                info='A{:.2} E{:.2}'.format(float(self.agreement),self.emotion)
            return 'Stage:{} {} {}'.format(self.type,unicode(self.ego).encode('ascii','replace'),info)

    class Factor(object):
        typs=InteractionRules.factors
        def __init__(self,typ,**kwargs):
            self.type=typ
            for i,j in kwargs.iteritems():
                setattr(self,i,j)
        def __str__(self):
            return 'Factor:{}'.format(self.type)

    def __init__(self):
        self.schema=nx.DiGraph()
        #self.conseq=nx.DiGraph()
        self.factors={}
        self.events={} #All the events of a stage
        self.event_source={} #The stages which are involved in shaping an event
        self.ethos={}
        self.by_actor=DataDict()
        #Important: order in which stages are run
        self.stage_priority={}

    def get_stage_priority(self,stage):
        '''Find the priority of a stage. If it is not in the dictionary
        stage_priority, look for the priority of its ancestors.'''
        cur=[stage]
        prior=self.stage_priority
        while cur:
            pcur=[prior[c] for c in cur if c in prior and prior[c]!=None]
            if pcur:
                return max(pcur)
            s=cur.pop(0)
            if s is None:
                continue
            nxt=self.schema.predecessors(s)
            if nxt:
                cur+=nxt
        return 0

    def add_stage(self,stage):
        if stage in self.schema.nodes():
            return
        self.schema.add_node(stage)
        #self.conseq.add_node(stage)
        self.factors[stage]=[]
        self.events[stage]=[]
        self.ethos[stage]=[]

    def add_edge(self,stage1,stage2):
        for s in (stage1,stage2):
            self.add_stage(s)
        self.schema.add_edge(stage1,stage2)


    def get_textdic(self):
        '''Get a matrix of which Stage will produce the text seen
        by actor i for the involvement of actor j in the interacton.
        Simply put, it is'''
        tdic=sparsemat(None)
        for a,nodes in self.by_actor.iteritems():
            for n in nodes:
                if n.type=='claim':
                    tdic[a][a]=n
                if n.type=='reac':
                    if n.verbal:
                        tdic[a][n.actor]=n
                if n.type=='perceived_claim':
                    tdic[a][n.actor]=n
                if n.type=='perceived_reac':
                    tdic[a][n.actor]=n
        for a,nodes in self.by_actor.iteritems():
            for n in nodes:
                if n.type=='interpret':
                    b=n.actor
                    if not b in tdic[a]:
                        tdic[a][b]=n
        return tdic

    def pass_events(self):
        '''The events have already been run privately
        while building the interaction.
        Now they need to be passed to all relevant handlers,
        to update graphics and sonon.'''
        for elem,evts in self.events.iteritems():
            for e in evts:
                user.evt.pass_event(e,self,ephemeral=True)

    def undo_events(self):
        '''Rolls back all events, starting from the leaves of the interaction.'''

        schema=self.schema
        leaves=[n for n,d in schema.out_degree().items() if d==0]
        cur=set(leaves)
        events=[]
        while cur:
            for c in tuple(cur):
                cur=cur.union(set(schema.predecessors(c)))
                cur.remove(c)
                if c in self.events:
                    events+= self.events[c]
                    #print c,self.events[c]
        cur=list(events)
        while cur:
            e=cur[0]
            if user.evt.go(e,0,shall_not_pass=True):
                cur.remove(e)
                #print e,[(c,e.states.node[e.state]['children_states'].get(c,"WUT")) for c in e.current_children(1)],e.state

class InteractionModel(object):
    '''Mechanics of the interaction'''
    Stage=Interaction.Stage
    Factor=Interaction.Factor

    def __init__(self, match):
        self.interactions=[]
        self.match=match
        self.rules=InteractionRules(match)
        self.actors=match.actors
        self.actgraph=match.data.actorgraph
        self.subgraph=match.data.actorsubgraphs

    def make_script(self,evt,scene):
        if 'claim' in evt.type:
            inter=self.process_claim(evt)
            script=InteractionScript(inter)
            inter.undo_events()
            script.parse_interaction(scene)
            return script

    def process_claim(self,claimevt,inter=None):
        '''Treatment of a claim proceeds in four stages:
                - A claims (truth or inference)
                - B perceives claim (add to subgraph)
                - B reacts (agreement)
                - A/C interprets reactions (add to subgraph)
        '''
        if inter is None:
            inter=Interaction()
            self.interactions.append(inter)
            for a in self.actors:
                inter.by_actor[a]=[]
                #inter.by_pov[a]=[]

        #local variables
        rules=self.rules
        actors=self.actors
        Stage=self.Stage
        match=self.match

        claimant=world.get_object(claimevt.actor)

        #Process claims and reactions in parallel
        #First do subclaims by priority order
        plist=[(p,c) for p,c in claimevt.priority_list(1) if c in claimevt.subclaims or c==claimevt]
        priority={}
        for p,c in plist:
            item=c.item
            claim=Stage('claim',item=item,actor=claimant,ego=claimant)
            if item.type=='node':
                claim.truth=c.decl.kwargs['truth']
            elif item.type=='link':
                claim.pattern=self.match.data.actorgraph[
                    c.actor].get_info(item,'pattern')
            inter.add_stage(claim)
            self.process_claim_to_reac(claim,inter)
            priority[claim]=p*100
        inter.stage_priority.update(priority)

        #Reactions are then interpreted in a way that depends on which
        #ones are verbal or not!
        for ego in actors:
            for act,stages in inter.by_actor.iteritems():
                if act==ego:
                    continue
                reacs=[r for r in stages if r.type=='reac']
                if not reacs:
                    continue
                #Perceive reaction is a comparatively trivial step
                preacs=[]
                for reac in reacs:
                    perceived_reac=self.perceive_reac(ego,act,reac)
                    preacs.append(perceived_reac)
                    inter.add_edge(reac,perceived_reac)
                    #TEMPORARY, AWAITING INTERPRETATION IMPLEMENTATION
                    #inter.add_edge(reac,perceived_reac)#TMP TMP
                    #self.prepare_stage(perceived_reac,inter) #TMP TMP

                #Interpretation of perceived reactions
                interpret=self.interpret_reacs(ego,act,preacs)
                for preac in preacs:
                    inter.add_edge(preac,interpret)
                self.prepare_stage(interpret,inter)
        self.make_ethos_effects(inter)
        return inter


    #SECOND PART OF CLAIM PROCESSING====================================


    def interpret_reacs(self,ego,actor,perceived_reacs):
        '''Ego perceives a bunch of reactions from actor (e.g.
        independent reactions for a link and its nodes)'''
        verbal={r:(r.verbal,getattr(r,r.verbal)) for r in perceived_reacs
            if r.verbal}
        nv={r:(r.agreement,r.emotion) for r in perceived_reacs
            if not r.verbal}
        nonverbal,mean=self.rules.discern_nonverbal(ego,nv)
        return self.Stage('interpret',ego=ego,actor=actor,
            verbal=verbal,nonverbal=nonverbal,mean=mean)


    def perceive_reac(self,ego,actor,reac):
        if reac.verbal=='agreement':
            agreement=reac.agreement
        else:
            agreement=self.rules.perceived_agreement(ego,reac)
        if reac.verbal=='emotion':
            emotion=reac.emotion
        else:
            emotion=self.rules.perceived_emotion(ego,reac)
        #print 'PERCEIVE REAC',ego,actor

        discovery=self.rules.perceived_discovery(ego,reac)
        perceived_reac=self.Stage('perceived_reac',ego=ego,actor=actor,
            item=reac.item, agreement=agreement,emotion=reac.emotion,
            verbal=reac.verbal, discovery=discovery)
        return perceived_reac



    #FIRST PART OF CLAIM PROCESSING====================================

    def process_claim_to_reac(self,claim,inter):
        '''Part of the processing that goes from the initial claim
        to the perceived reactions.'''
        item=claim.item
        claimant=claim.actor

        self.prepare_stage(claim,inter)
        #Tree of reactions
        for act2 in self.actors:
            if act2==claimant:
                continue

            #Perceived claim
            perceived_claim=self.perceive_claim(act2,claimant,claim)
            inter.add_edge(claim,perceived_claim)
            self.prepare_stage(perceived_claim,inter)

            #Reaction to perceived claim
            reac=self.react_claim(act2,perceived_claim,inter)
            inter.add_edge(perceived_claim,reac)
            self.prepare_stage(reac,inter)

    def perceive_claim(self,ego,actor,claim):
        '''Creates the perceived_claim'''
        match=self.match
        item=claim.item
        perceived_claim=self.Stage('perceived_claim',ego=ego,actor=actor,
            item=item)

        if item.type=='node':
            perceived_claim.truth=self.rules.perceived_truth(ego,claim,match.cast)
        elif item.type=='link':
            perceived_claim.pattern=claim.pattern

        #Belief of actor 2
        subg=self.subgraph[ego][ego]
        actg=self.actgraph[ego]

        newinfos={}
        #Is the claimed item already known to reactant?
        if subg.contains(item):
            #Already thought of during this conversation
            discovery=0.
        elif actg.contains(item):
            #Known before but not thought of
            if item.type=='node':
                newinfos.update(self.rules.belief_revision_under_influence(
                    ego,perceived_claim,actg))
            discovery=1./2
        else:
            #Discovery
            if item.type=='node':
                #bias here is created through irrational influence
                newinfos.update(self.rules.belief_creation_under_influence(
                    ego,perceived_claim))
            elif item.type=='link':
                newinfos.update(self.rules.link_discovery(ego,perceived_claim))
            discovery=1.
        perceived_claim.discovery=discovery
        perceived_claim.egoinfos=newinfos
        #if newinfos.get('pattern',None) == 'Unknown':
            #perceived_claim.pattern='Unknown'
        return perceived_claim

    def react_claim(self,ego,perceived_claim,inter):
        subg=self.subgraph[ego][ego]
        cast=self.match.cast
        actor=perceived_claim.actor
        item=perceived_claim.item
        #Agreement of reactant
        factors=inter.factors[perceived_claim]
        if item.type=='node':
            agreement=self.rules.agreement(ego,perceived_claim,subg)
        elif item.type=='link':
            agreement=self.rules.agree_inference(ego,perceived_claim)
        emotion=self.rules.emotion(ego,factors)
        verbal=self.rules.verbalisation(agreement,emotion)
        return self.Stage('reac',item=item,ego=ego,agreement=agreement,
            emotion=emotion,verbal=verbal,actor=actor,discovery=perceived_claim.discovery)

    #GENERAL PROCESSING====================================

    def prepare_stage(self,stage,inter):
        '''Central function that stages the preparation of a stage
        after it has been created by a specialized function.'''
        inter.by_actor[stage.ego].append(stage)
        self.create_logic_evts(stage,inter)
        self.run_logic_evts(stage,inter)
        #The logic events must be run first to get a complete list
        #of all repercussions. Those are then analyzed in terms of factors.
        self.create_factors(stage,inter)
        self.run_factor_evts(stage,inter)

    def create_factors(self,stage,inter):
        '''Parse everything that has happened into discrete, relevant factors
        (sort of events) picked from the list InteractionRules.factors.
        Things such as conflicts couldn't be ascertained in the preparation
        stage because they may be affected by chains of logical_events.'''
        facs=[]
        facevts={}
        Fac=self.Factor
        if stage.type=='perceived_claim':
            ego=stage.ego
            item=stage.item
            actor=stage.actor
            sgraph=self.match.data.actorsubgraphs[ego][ego]
            othgraph=self.match.data.actorsubgraphs[ego][actor]
            if stage.discovery==1:
                facs.append(Fac('discovery',ego=ego,actor=actor,item=item) )
            tr=self.match.ruleset.truth_value
            if tr(sgraph.get_info(item,'truth'))*tr(
                        othgraph.get_info(item,'truth'))<0:
                facs.append(Fac('opinion_conflict',ego=ego,actor=actor,item=item) )

        changes={}
        for evt in inter.events[stage]:
            for e in [evt]+list(evt.all_children()):
                if e.state==0:
                    continue
                if 'add' in e.type:
                    if 'pattern' in e.infos and e.infos['pattern']=='Unknown':
                        facs.append(Fac('unknown_pattern',item=e.item,
                                actor=stage.actor,ego=stage.ego))
                if 'change' in e.type:
                    dif={i:j-e.oldinfo[i] for i,j in e.infos.iteritems()}
                    changes.setdefault((e.item,e.data),[]).append(dif)
        #information changes
        for xs,cs in changes.iteritems():
            item,data=xs
            actor=data.owner
            selfgraph=self.match.data.actorsubgraphs[actor][actor]
            finalchange={i:sum(c[i] for c in cs if i in c) for i in item.dft }
            for i,dif in finalchange.iteritems():
                if dif==0:
                    continue
                facinfos={'ego':actor,'actor':stage.actor}
                if i=='truth' and data==selfgraph:
                    datinf=data.get_info(item)
                    shift= self.rules.interpret_truth_change(actor,dif,datinf)
                    if shift:
                        #Consequences of opinion shift
                        if self.match.canvas.get_info(item,'claimed')==actor.trueID :
                            #Concession
                            facs.append(Fac('concede',item=item,**facinfos))
                        facs.append(Fac(shift,item=item,dif=dif,**facinfos))
                        if datinf.get('terr',None):
                            #Activation/Deactivation of invested territory
                            activ= datinf['terr']*self.match.ruleset.truth_value(datinf['truth'])
                            if activ:
                                facs.append(Fac('teri_activ' ),val=activ,**facinfos)
                if i=='terr' and data==selfgraph:
                    #Change in invested territory
                    facs.append(Fac('teri_change' ),val=dif,**facinfos )
                if i=='bias' and data!=selfgraph:
                    facs.append(Fac('reeval_bias', val=dif, ego=actor,actor=stage.actor ) )
                    #print 'dif bias',dif,actor,item,data,data.get_info(item,'bias')
        inter.factors[stage][:]=facs
        for f in facs:
            inter.events[f]=[]
            inter.ethos[f]=[]
        self.create_factor_events(facs,inter)
        return


    def run_logic_evts(self,stage,inter):
        #print '\n\n==================\n{}\n=================='.format(stage)
        events=inter.events[stage]
        self.run_evts(events,inter)

    def run_factor_evts(self,stage,inter):
        events=(evt for f in inter.factors[stage]
                for evt in inter.events[f])
        self.run_evts(events,inter)

    def run_evts(self,events,inter):
        '''Local version of evt_do, without passing anything.
        It might be more elegant to actually use evt_do'''


        priorities={e:max(inter.get_stage_priority(r) for r in
                inter.event_source.get(e,None)) for e in events }

        for e in sorted(events,key=lambda x:priorities[x],reverse=True):
            #print '\n\n==================',e, e.priority_list(1)
            user.evt.do(e,self,2,shall_not_pass=True)

        return



    def create_logic_evts(self,stage,inter):
        '''This looks only at the logical consequences
        of a stage. The psychological consequences are processed
        via the factors, cf. create_factors.'''
        if  inter.events.get(stage):
            return False
        match=self.match
        ego=stage.ego
        #print stage
        subg=self.subgraph[ego][ego]
        subact=self.subgraph[ego][stage.actor]
        actg=self.actgraph[ego]
        evts=[]
        link_discoveries=[] #PERCEIVED REACTIONS that betray the discovery of a new link

        if 'perceived_claim' == stage.type:
            #Ego perceives claim by actor
            item=stage.item
            egoinfos=stage.egoinfos
            actinfos={}
            evt=None
            if stage.discovery>0:
                if stage.discovery==1:
                    #Add to actorgraph
                    devt=AddEvt(item,actg)
                    evts.append(devt)
                #Add to selfgraph
                evt=AddEvt(item,subg,infos=egoinfos)
            elif egoinfos:
                #Change in selfgraph
                evt=ChangeEvt(item,subg,**egoinfos)
            if evt:
                evts.append(evt)

            if item.type=='node':
                #Deduce actor's' bias from the links known to ego
                #but with the truth values that ego believes actor has
                actinfos['truth']=stage.truth
                actinfos['stated_truth']=stage.truth
                egotruth=egoinfos.get('truth',subg.get_info(item,'truth'))
                pbias= stage.truth-match.ruleset.calc_truth(item,subg,
                    subact,extrapolate=1,bias=0)
                actinfos['bias']=pbias
            #Adding item to subgraph[self][other]
            oevt=AddEvt(item,subact,infos=actinfos)
            evts.append(oevt)

        if 'reac' == stage.type:
            #
            pass

        if 'interpret' == stage.type:
            #Ego interpets reaction by actor
            to_add={}
            verbal=stage.verbal
            nonverbal=stage.nonverbal
            mean=stage.mean #average agreement and emotion
            for r,i in verbal.iteritems():
                actor=r.actor
                item=r.item
                if i[0]=='agreement':
                    to_add[(item,r)]=i[1]
                else:
                    to_add[(item,r)]=mean[0]
            for r,i in nonverbal.iteritems():
                actor=r.actor
                g=self.subgraph[ego][stage.actor]
                item=r.item
                if not (item,r) in to_add:
                    to_add[(item,r)]=i[0]
            for item,reac in to_add:
                agree=to_add[(item,reac)]
                actinfos={}
                if item.type=='link':
                    if not agree:
                        actinfos['pattern']='Unknown'
                elif item.type=='node':
                    tmpstage=self.Stage('tmp',item=item,agreement=agree,
                        ego=ego,actor=stage.actor)
                    #Deduce truth from degree of agreement
                    truth=self.rules.truth_from_agreement(
                        ego,tmpstage,subact)
                    actinfos['truth']=truth
                    actinfos['stated_truth']=truth
                    egotruth=subg.get_info(item,'truth')
                    #Deduce bias
                    pbias= truth-match.ruleset.calc_truth(item,subg,
                        subact,extrapolate=0,bias=0)
                    actinfos['bias']=pbias
                evt=AddEvt(item,subact,infos=actinfos)
                evts.append(evt)
                inter.event_source.setdefault(evt,[]).append(reac)
                if reac.discovery and item.type=='link':
                    link_discoveries.append(evt)



        #If there are AddEvts/ChangeInfosEvts, attach them to TruthCalcEvts
        #which take their place in the event list
        per_item={}
        for evt in tuple(evts):
            if 'add' in evt.type or 'change' in evt.type and 'truth' in evt.infos:
                if evt.data == actg and not self.rules.update_true_beliefs:
                    #dont update truth in actorgraph if rules forbid it
                    continue
                #If a link has been discovered by actor, truthcalc must ignore_stated
                #because the stated_truth from before may be different from
                #what actor now believes, knowing the link.
                ignore_stated= evt in link_discoveries
                item=evt.item
                tevt=TruthCalcEvt(item,subg,evt.data,ignore_stated=ignore_stated)
                tevt.add_sim_child(evt,priority=2)
                per_item.setdefault(item,[]) #List to group truthcalc relating to same item
                per_item[item].append( tevt)
                evts.remove(evt)
                inter.event_source[tevt]=inter.event_source.get(evt,[None])
                if evt in link_discoveries:
                    cevt=ReactLinkDiscoveryEvt(evt.item,subg,evt.data)
                    tevt.add_sim_child(cevt,priority=1)
                    inter.event_source[cevt]=inter.event_source[tevt]

                #print ' >P:',evt,evt.infos
            inter.event_source.setdefault(evt,[stage])


        #Group truthcalc events concerning the same item
        for item in per_item:
            tcalc=per_item[item]
            for e1 in tuple(tcalc):
                for e2 in tuple(tcalc):
                    if e2==e1:
                        continue
                    if e1.tgtgraph in e2.tgtgraph.precursors():
                        tcalc.remove(e2)
                        e1.add_sim_child(e2,priority="enclosed")
            evts+=tcalc
        inter.events[stage]=evts

    def create_factor_events(self,facs,inter):
        match=self.match
        for f in facs:
            evts=[]
            if f.type=='concede':
                item=f.item
                ego=f.ego
                actor=f.actor
                infos=match.canvas.get_info(item)
                evt=ChangeInfosEvt(item,match.data.convgraph,claimed=actor.trueID)

            inter.events[f]+=evts

    def make_ethos_effects(self,inter):
        match=self.match
        for stage,factors in inter.factors.iteritems():
            for f in factors:
                effects=[]
                effect= {}
                #Format ethos effects from the rules in the universal format
                psy=self.rules.psy[f.ego].ethos_effects([f]).iteritems()
                for i,j in psy:
                    if i=='prox':
                        j={f.actor.trueID:j}
                    effect[(f.ego,i)]=j

                effects.append( effect)

                if f.type=='concede' and not 'shift' in f.type:
                    #Add ethos effects from the node, in the same universal format
                    effects.append(self.node_ethos_effects(f.item,f))
                inter.ethos[f]+=effects

            if stage.type=='claim':
                inter.ethos[stage].append(self.node_ethos_effects(stage.item,stage))


    def node_ethos_effects(self,item,evt):
            #EFFECTS ATTACHED TO NODE, ACTIVATED UPON CLAIMED/CONCEDED
        match=self.match
        info = match.canvas.get_info(evt.item)
        effects={}
        if evt.type=='concede':
            ego=world.get_object(evt.actor) #the person who is conceded TO is ego
        else:
            ego=world.get_object(evt.ego)
        for e in info.get('effects',()):
            targets=e.target
            if targets=='claimer':
                targets=ego,
            elif targets=='hearer':
                targets=tuple(i for i in match.cast.actors if i != ego)
            elif not hasattr(targets,'__iter__'):
                targets=targets,
            val=e.val
            if e.res=='prox' and not hasattr(val,'keys'):
                val={ego:e.val}
            for target in targets:
                if hasattr(val,'keys') and target in val:
                    continue
                self.add_effect( effects, (target,e.res), val )
        return effects



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