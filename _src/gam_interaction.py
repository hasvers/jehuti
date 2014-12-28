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


from gam_globals import *

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
        eag=infosrc.get_info('prox',ego)[actor]- infosrc.get_info('prox',actor)[ego]
        return (eag+1.)/2

    def difface(self,actor,infosrc):
        '''Face difference (ego-actor), rescaled in [0,1]'''
        difinfosrc.get_info('face',ego)- infosrc.get_info('face',actor)
        return (dif+1)/2.

    def demonstrativeness(self,actor,infosrc):
        '''How likely ego is likely to speak their mind to actor.'''
        eagerness=self.eagerness(actor,infosrc)
        confidence=self.difface(actor,infosrc)
        return eagerness*confidence

    def emotion(self,factors,infosrc):
        '''Compute the emotion resulting from a series of factors.
        Emotion is a complex variable, with abs(emo) the intensity
        and arg(emo) the hue.
        Russel and Barret model of core affect:
            Re: pleasantness
            Im: activation'''
        emo=0+0J
        pleas=0 #How pleasant the experience is
        activ=0 #How busy the experience is
        for e in factors:
            if e.type=='ethos':
                pleas+=e.val
            elif e.type=='opinion_divergence':
                pleas-=.5
                activ+=1.
            elif e.type=='concede':
                pleas-=1.
                activ+=1.
            elif e.type=='opinion_change':
                active+=1.
            elif e.type=='unknown_pattern':
                pleas-=1.
            elif e.type=='investerr_change':
                active+=1.
            elif e.type=='investerr_activ':
                #if invested territory gets activated/lost,
                #huge emotional impact
                please+=3*e.val
        emo=pleas/5.+1J*activ/8.
        return emo

    def trust_opinon(self,actor,infosrc):
        '''How likely ego is likely to trust actor's opinion
        irrationally, and thus become biased. Depends on actor's
        authority, on ego's' prox to actor, and on ego's eagerness
        (which also contains the prox, but both aspects contribute).'''
        prox=infosrc.get_info('prox',ego)[actor]
        eagerness=self.eagerness(actor,infosrc)
        authority=infosrc.get_info('face',actor)
        return authority/2.+(prox+eagerness)/4


    def pathos_effectiveness(self,ego,actor):
        #IMPORTANT: reverse order of arguments compared to gam_rules
        '''How effective is an appeal to pathos on ego by actor.
        Increase with proximity to actor, decreases with ego's territory.'''
        if actor==ego:
            return 1.
        egoinf=self.cast.get_info(ego)
        actorinf=self.cast.get_info(actor)
        prox=egoinf['prox'][actor]
        return .5*(prox)*(2-actorinf['terr'])



class InteractionRules(object):

    factors=('ethos','opinion_divergence','concede','opinion_change',
            'unknown_pattern','reeval_bias','investerr_activ',
            'investerr_change'
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

    def perceived_agreement(self,ego,reac,infosrc):
        '''When ego receives a reac with a given agreement,
        how much error is there on it in the perceived_claim?'''
        baseval=reac.agreement
        percep=infosrc.get_info(ego,'perc')
        chance=rnd.uniform(-1,1)
        return baseval*(1.+(1-percep)*chance)

    def truth_from_agreement(self,ego,perceived_reac,infosrc):
        '''Make assumption on someone else's opinion based on perceived agreement.'''
        baseval=infosrc.get_info(perceived_reac.item,'truth')
        agr=perceived_reac.agreement
        t= 0.5+ (baseval-.5)*min(max(-1,agr),1)
        return max(0,min(1,t))

    def belief_revision_under_influence(self,ego,perceived_claim,infosrc):
            #=> Some influence from claimant who can distort or encourage remembrance
        trust=self.psy[ego].trust_opinon(ego,perceived_claim.actor,self.match.cast)
        egotruth=infosrc.get_info(ego,'truth')
        if trust>.5:
            return {'bias': trust*(perceived_claim.truth-egotruth)/2 }
        else:
            return {}

    def belief_creation_under_influence(self,ego,perceived_claim,infosrc):
            #(wanting to believe/disbelieve the perceived claim depending on
            #ethos and proximity)
        trust=self.psy[ego].trust_opinon(ego,perceived_claim.actor,self.match.cast)
        egotruth=infosrc.get_info(perceived_claim.item,'truth')
        if trust>.5:
            return {'bias': trust*(perceived_claim.truth-egotruth) }
        else:
            return {}

    def agreement(self,ego,perceived_claim,consequences,infosrc):
        '''Three components to agreement: opinion difference,
        whether the opinion was created just now,
        and demonstrativeness.'''
        match=self.match
        egotruth=infosrc.get_info(perceived_claim.item,'truth')
        claimtruth=perceived_claim.truth
        agreement=abs(egotruth+claimtruth -1)/2.
        agreement*=perceived_claim.discovery
        agreement*=self.psy[ego].demonstrativeness(match,reac,claimant)
        return agreement

    def emotion(self,ego,perceived_claim,consequences):
        return self.psy[ego].emotion(consequences,self.match)



    def ethos_effects(self,factors):
        '''Compute the ethos effects resulting from various factors.'''
        face,terr,prox=0,0,0
        for e in factors:
            if e.type=='opinion_divergence':
                prox-=.05
            elif e.type=='concede':
                face-=.1
            elif e.type=='opinion_change':
                terr-=.05
            elif e.type=='unknown_pattern':
                prox-=.05
                face-=.05
        return {'face':face,'terr':terr,'prox':prox}


#### MECHANICS #####=============================================================


class Interaction(object):

    class Stage(object):
        def __init__(self,typ,**kwargs):
            self.type=typ
            for i,j in kwargs.iteritems():
                setattr(self,i,j)

    class Factor(object):
        typs=InteractionRules.factors
        def __init__(self,typ,**kwargs):
            self.type=typ
            for i,j in kwargs.iteritems():
                setattr(self,i,j)

    def __init__(self):
        self.schema=nx.DiGraph()
        self.conseq=nx.DiGraph()
        self.factors={}
        self.match_events={}
        self.by_actor={}


    def add_stage(self,stage):
        self.schema.add_node(stage)
        self.conseq.add_node(stage)

    def add_factor(self,factor,stage):
        self.conseq.add_node(factor)
        self.conseq.add_edge(stage,factor)


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



class InteractionModel(object):
    '''Mechanics of the interaction'''
    Stage=Interaction.Stage
    Factor=Interaction.Factor

    def __init__(self, match):
        self.interactions=[]
        self.match=match
        self.rules=InteractionRules(match)
        self.actors=match.actors
        self.actgraph=match.actorgraph
        self.subgraph=match.actorsubgraphs


    def process_claim(self,claimevt,inter=None):
        if inter is None:
            inter=Interaction()
            self.interactions.append(inter)
        item=claimevt.item
        if item.type=='node':
            claim=self.process_node_claim(claimevt,inter)
        for sc in claim.subclaims:
            subclaim=self.process_claim(sc,inter)
            self.add_edge(claim,subclaim)

        return claim


    def process_node_claim(self,claimevt,inter):
        #local variables
        rules=self.rules
        actors=self.actors
        node=claimevt.item
        Stage=self.Stage

        claim=Stage('claim',node=claimevt.item,actor=claimevt.actor,truth=claimevt)
        inter.schema.add_node(claim)
        claimant=claimevt.actor

        #Tree of reactions
        for act2 in actors:
            if act2==claimant:
                continue


            #Reaction to perceived claim
            perceived_claim=self.perceive_claim(act2,claimant,claim)
            inter.add_edge(claim,perceived_claim)
            reac=self.react_node_claim(act2,claimant,perceived_claim)
            inter.add_edge(perceived_claim,reac)

            #Reaction is then interpreted
            for act3 in actors:
                if act3==act2:
                    continue
                #Interpretation of perceived reaction
                perceived_reac=self.perceive_reac(act3,act2,reac)
                inter.add_edge(reac,perceived_reac)


                interp=self.interpret_node_reac(act3,act2,perceived_reac)
                inter.add_edge(perceived_reac,interp)

    def react_node_claim(self,ego,actor,perceived_claim):
        #React to some *perceived* claim
        inter=self.interactions[-1]
        #Belief of actor 2
        subg=self.subgraph[ego][ego]
        actg=self.actgraph[ego]

        #Is the claimed node already known to reactant?
        if node in subg:
            #Already thought of during this conversation
            newinfos={}
            discovery=0.
        elif node in actg:
            #Known before but not thought of
            newinfos=self.rules.belief_revision_under_influence(ego,perceived_claim)
            discovery=1./2
        else:
            #Discovery: bias here is created through irrational influence
            newinfos=self.rules.belief_creation_under_influence(ego,perceived_claim)
            discovery=1.
        perceived_claim.discovery=discovery

        #Include effect of logical cascades!
        #(especially if it leads to feedback loop
        #changing the belief on the claimed node)
        if discovery:
            #simulate the effect of changing the belief
            for n in self.logical_cascade(ego,newinfos,match):
                consequences.append( n)
                inter.add_consequence(perceived_claim)


        #Agreement of reactant
        agreement=self.rules.agreement(ego,perceived_claim,consequences,match)
        emotion=self.rules.emotion(ego,perceived_claim,consequences,match)

        return self.Stage('reac',actor=reac,newinfos=newinfos,discovery=discovery,
                    agreement=agreement,consequences=consequences)

    def interpret_node_reac(self,ego,actor,perceived_reac):
        return self.Stage('interpret',actor=act3)

    def logical_cascade(newinfos):
        cevt=ChangeInfosEvt()


    def perceive_claim(self,ego,actor,claim):
        perceived_claim=self.Stage('perceived_claim',ego=ego,actor=actor,
            belief=belief,discovery=discovery,
                    agreement=agreement,consequences=consequences)
        perceived_claim.truth=self.
        return perceived_claim

    def perceive_reac(self,ego,actor,reac):
        perceived_reac=reac.copy()
        #The perceived agreement is a function that tends to
        #the real agreement for large values of it
        #but is muddled
        perceived_reac.agreement=
        return perceived_reac

    def make_ethos_effects(self,scheme):
        return

    def make_match_events(self,scheme):
        return

