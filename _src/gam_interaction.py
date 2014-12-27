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


class Interaction(object):

    def __init__(self):
        self.schema=nx.DiGraph()

class InteractionModel(object):


    class Step(object):
        def __init__(self,typ,**kwargs):
            self.type=typ
            for i,j in kwargs.iteritems():
                setattr(self,i,j)

    def __init__(self, match):
        self.interactions=[]
        self.match=match

    def process_claim(self,claimevt,inter=None):
        if inter is None:
            inter=Interaction()

        item=claimevt.item
        if item.type=='node':
            claim=self.process_node_claim(claimevt,inter)
        for sc in claim.subclaims:
            subclaim=self.process_claim(sc,inter)
            self.add_edge(claim,subclaim)

        return claim


    def process_node_claim(self,claimevt,inter):
        #local variables
        match=self.match
        rules=match.ruleset
        actors=match.actors
        actgraph=match.actorgraph
        subgraph=match.actorsubgraphs
        node=claimevt.item

        claim=Step('claim',node=claimevt.item,actor=claimevt.actor,truth=claimevt)
        inter.schema.add_node(claim)
        claimant=claimevt.actor

        #Tree of reactions
        for act2 in actors:
            if act2==claimant:
                continue


            #Reaction to perceived claim
            perceived_claim=self.perceive_claim(act2,claimant,claim)
            reac=self.react_node_claim(act2,claimant,perceived_claim)
            inter.add_edge(claim,reac)

            #Reaction is then interpreted
            for act3 in actors:
                if act3==act2:
                    continue
                #Interpretation of perceived reaction
                perceived_reac=self.perceive_reac(act3,act2,reac)


                interp=self.interpret_node_reac(act3,act2,perceived_reac)
                inter.add_edge(reac,interp)

    def react_node_claim(reac,claimant,perceived_claim):
        #React to some *perceived* claim

        #Belief of actor 2
        subg=subgraph[reac][reac]
        actg=actgraph[reac]

        #Is the claimed node already known to reactant?
        if node in subg:
            #Already thought of during this conversation
            belief=subg.get_info(node,'truth')
            discovery=False
        elif node in actg:
            #Known before but not thought of
            #=> Some influence from claimant who can distort or encourage remembrance
            belief=rules.belief_revision_under_influence(match,node,reac,perceived_claim)
            discovery='recall'
        else:
            #Discovery: bias here is created through irrational influence
            #(wanting to believe/disbelieve the perceived claim depending on
            #ethos and proximity)
            belief=rules.belief_creation_under_influence(match,node,reac,perceived_claim)
            discovery=True



        #Include effect of logical cascades!
        #(especially if it leads to feedback loop
        #changing the belief on the claimed node)
        if discovery:
            #simulate the effect of changing the belief
            for n in self.logical_cascade(belief):
                consequences.append( )
        #If there are many consequences

        #Agreement of reactant
        agreement=rules.logical_agreement(match,belief,perceived_claim)
        agreement*=rules.demonstrativeness(match,reac,claimant)
        return Step('reac',actor=reac,belief=belief,discovery=discovery,
                    agreement=agreement,consequences=consequences)

    def interpret_node_reac(self,perceiver,reactant,perceived_reac):
        return Step('interpret',actor=act3)


    def perceive_claim(self,perceiver,claimant,claim):
        perceived_claim=reac.copy()
        perceived_claim.truth=
        return perceived_claim

    def perceive_reac(self,perceiver,reactant,reac):
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

