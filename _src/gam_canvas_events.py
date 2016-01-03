# -*- coding: utf-8 -*-

from gam_import import *

class LogicEvent(Event):
    '''Superclass for events for

    1) logical consequences, generally bound (with low priority)
    to an AddEvt or ChangeInfosEvt concerning logic-related elements
    (bias, truth, link logic, new or disputed link).

    2) other processes that may share traits of such events (e.g. Match events)
    '''

    dft={
        'item':None,
        }

    def __init__(self,item,**kwargs):
        super(LogicEvent, self).__init__(**kwargs)
        self.item=item
        self.add_state(2,pred=1)
        self.type='logic_evt'

    # when using do or undo, put match as second argument after state

    def prepare(self,edge,match,*args,**kwargs):
        if edge ==(0,1) :
            self.prep_init(match)
        if edge ==(1,0) :
            self.prep_uninit(match)
        if edge ==(1,2) :
            self.prep_do(match)
        if edge ==(2,1) :
            self.prep_undo(match)
        #print 'prep',self,edge, self.states.node[edge[1]]['children_states']

    def run(self,state,*args,**kwargs):
        #print 'run',self,state
        return True

    def do_prior(self,evt,do,undo,prior):
        if not prior:
            return
        if hasattr(prior,'keys'):
            dop=prior[do]
            undop=prior[undo]
        else :
            dop=undop=prior
        self.states.node[do]['priority'][evt]=dop
        self.states.node[undo]['priority'][evt]=undop


    def child_add(self,item,data,do=2,undo=1,**kwargs):
        evt=AddEvt(item,data,infos=kwargs,assess=True,addrequired=True)
        evt.parent=self
        if self.check_duplicate(do,evt,**kwargs):
            return False
        self.states.node[do]['children_states'][evt]=1
        self.states.node[undo]['children_states'][evt]=0
        if do and undo : #neither is 0
            self.states.node[0]['children_states'][evt]=0
        self.do_prior(evt,do,undo,kwargs.pop("priority",{do:1,undo:-1}  ))


    def child_chginfo(self,item,data,do=2,undo=1,**kwargs):
        evt=ChangeInfosEvt(item,data,**kwargs)
        evt.parent=self
        if self.check_duplicate(do,evt,**kwargs):
            return False
        self.states.node[do]['children_states'][evt]=1
        self.states.node[undo]['children_states'][evt]=0
        if do and undo : #neither is 0
            self.states.node[0]['children_states'][evt]=0
        self.do_prior(evt,do,undo,kwargs.pop("priority",False))


    def prep_init(self,*args,**kwargs):
        pass
    def prep_uninit(self,*args,**kwargs):
        pass
    def prep_do(self,*args,**kwargs):
        pass
    def prep_undo(self,*args,**kwargs):
        pass

class TruthCalcEvt(LogicEvent):
    '''Event called whenever bias changes or new link added, to recompute truth
    throughout the graph.'''

    dft={
        'tgtgraph':None,
        'refgraph':None,
        'item':None,
        }

    def __init__(self,item,refgraph,tgtgraph=None,**kwargs):
        super(TruthCalcEvt, self).__init__(item,**kwargs)
        self.refgraph=refgraph
        if tgtgraph is None:
            tgtgraph=refgraph
        self.tgtgraph=tgtgraph
        self.type='truthcalc'
        self.ignore_stated=kwargs.get('ignore_stated',False)
        self.changevts={}

    def __str__(self):
        item,refgraph,tgtgraph=self.item,self.refgraph,self.tgtgraph
        if refgraph!=tgtgraph:
            return "TruthCalc {} {} {}".format(item,refgraph,tgtgraph)
        else:
            return "TruthCalc {} {}".format(item,refgraph)

    def prep_do(self,match,*args,**kwargs):
        prep= self.truth_calc(match,self.item,self.refgraph,self.tgtgraph)
        #if not prep:
            #print '\n===== FAILED PREP',self,self.all_children()
        return True

    #def run(self,state,*args,**kwargs):
        #print 'Run',state, self,[str(i) for i in self.states.node[1]['children_states'] ]
        #return 1

    def truth_calc(self,match, item,graph=None,sub=None,track=None,tracklist=None):
        '''Core function for recomputing truth values, starting from the root_item
        of the TruthCalcEvt, then going by recurrence through every one of its consequences.
            Graph is the graph that the current actor believes to be true
            Sub is the graph for which truths are evaluated'''
        #track allows to track logical cycles
        if track is None:
            track={}
            tracklist=[]
        srceff=match.ruleset.link_effect_from_source
        tgteff=match.ruleset.link_effect_from_target
        if graph is None:
            graph=match.canvas.active_graph
        if sub is None:
            sub=graph
        if item.type=='link':
            s,t=item.parents
            logic=graph.get_info(item,'logic')
            #COMMENTED BELOW: WOULD BE USEFUL IF LINKS COULD CHANGE LOGIC
            #AS SUCH, USELESS (but implemented for editor in gam_Canvas)
            #if logic[2] or logic[3]:
                #reverse=self.truth_calc(s,graph,sub,track,tracklist)
            #else:
                #reverse=True
            #return self.truth_calc(t,graph,sub,track,tracklist) and reverse
            if srceff(graph.get_info(s,'truth'),logic ):
                return self.truth_calc(match,t,graph,sub,track,tracklist)
            elif tgteff(graph.get_info(t,'truth'),logic ):
                return self.truth_calc(match,s,graph,sub,track,tracklist)
            else:
                return 0

        #Truth inferred from the graph's logic
        truth=match.ruleset.calc_truth(item,graph,sub,extrapolate=0)

        #current value of the truth ####POTENTIAL BREAK: was this sub or graph?
        prevtruth=sub.get_info(item,'truth')

        #If the graph is a model of someone else's mind, rather than own belief,
        #there may be stated truths, i.e. values of which we are sure for the
        #other. Instead it is the other's underlying BIAS that is recomputed
        #unless this event is flagged to ignore this. This flagging is used
        #when computing the effect on the representation  of a NEW information,
        #i.e. when we know that someone just learned about a new link and we
        #want to know how this has transformed their stated truths.
        if self.ignore_stated:
            statedtruth=None
        else:
            statedtruth= sub.get_info(item,'stated_truth')
        if not statedtruth is None:
            should_have_truth=match.ruleset.calc_truth(item,graph,sub,extrapolate=1,bias=0)
            bias=statedtruth-should_have_truth
            prevbias=sub.get_info(item,'bias')
            #print 'truth of {} is {} should be {} hence bias {} (before, {})'.format(item,truth, should_have_truth,bias,prevbias)
            if prevbias!=bias:
                evt=ChangeInfosEvt(item,sub,bias=bias,source='biascalc')
                #print 'bias change {} to {}'.format(prevbias,bias),item,should_have_truth,statedtruth, sub
                self.add_child(evt,{0:0,2:1},priority={0:5,'else':-1})
            return 0

        #print 'glappy:', item,graph.name,sub.name,truth,prevtruth
        if truth==prevtruth and track:
            return 0
        #print 'truth change',truth,prevtruth,item, sub,sub.get_info(item,'truth'),graph
        if item in track:
            basetruth=track[item][0]
            assert track[item][1]==prevtruth #else there is something strange going on
            if truth==basetruth or (truth-basetruth)*(prevtruth-basetruth)<0:
                if truth==basetruth:
                    print 'alternating circle'
                print 'reductio ad absurdum'
                #reductio ad absurdum: the initial change causes a contradiction, cancel all changes
                #cancel
                for i in tracklist[tracklist.index(item):]:
                    if sub.get_info(i,'truth')!=track[i][0]:
                        self.set_change(i,sub,truth=track[i][0],source='truthcalc')
                        track[i]=(track[i][0],track[i][0])
                return 0
            else:
                if abs(truth-basetruth)>abs(prevtruth-basetruth):
                    print 'diverging cycle'
                    #virtuous circle, will saturate at 0 or 1, might as well set it right now
                    #unless more changes are to come (truth_value is changed by the circle)
                    if match.ruleset.truth_value(truth)== match.ruleset.truth_value(prevtruth):
                        nt=(1.+match.ruleset.truth_value(truth))/2

                        self.set_change(i,sub,truth=nt,source='truthcalc')
                        track[item]=(basetruth,nt)
                        return 0
                else:
                    print 'converging cycle', basetruth,prevtruth,truth
                    #attenuating effect, will converge, no problem

        if truth!= prevtruth:

            self.set_change(item,sub,truth=truth,source='truthcalc')
            #print 'set truth',item.name,truth, 'from' ,prevtruth, 'in', sub
        track[item]=(prevtruth,truth)
        tracklist.append(item)
        if match.ruleset.truth_value(truth)!= match.ruleset.truth_value(prevtruth):
            for l in sub.links.get(item,[]):
                logic=sub.get_info(l,'logic')
                if l.parents[0]==item:
                    if srceff(truth,logic)!=srceff(prevtruth,logic):
                        self.truth_calc(match,l.parents[1],graph,sub,track,tracklist)
                elif tgteff(truth,logic)!=tgteff(prevtruth,logic):
                    self.truth_calc(match,l.parents[0],graph,sub,track,tracklist)

    def set_change(self,item,sub,truth,source):
        if item in self.changevts:
            #In case we backtrack on a change
            old=self.changevts[item]
            del self.changevts[item]
            self.rem_child(old)
        infos={'truth':truth}
        if self.ignore_stated:
            #Recompute the stated
            infos['stated_truth']=truth
        evt=ChangeInfosEvt(item,sub,source='truthcalc',**infos)
        self.add_child(evt,{0:0,2:1},priority={0:5,2:-1})



class ReactLinkDiscoveryEvt(Event):
    #If ego realizes that someone DID NOT know a link before,
    #reevaluate ego's opinion of their bias: compute what ego thinks
    #is their bias WITHOUT this link.

    dft={
        'tgtgraph':None,
        'refgraph':None,
        'item':None,
        }


    def __init__(self,item,refgraph,tgtgraph=None,**kwargs):
        super(ReactLinkDiscoveryEvt, self).__init__(**kwargs)
        self.item=item
        self.refgraph=refgraph
        if tgtgraph is None:
            tgtgraph=refgraph
        self.tgtgraph=tgtgraph
        self.type='reactlinkdiscovery'

    def __str__(self):
        item,refgraph,tgtgraph=self.item,self.refgraph,self.tgtgraph
        if refgraph!=tgtgraph:
            return "ReactLinkDiscovery {} {} {}".format(item,refgraph,tgtgraph)
        else:
            return "ReactLinkDiscovery {} {}".format(item,refgraph)


    def prepare(self,edge,match,*args,**kwargs):
        ref=self.refgraph
        tgt=self.tgtgraph
        item=self.item
        if edge==(0,1):
            for node in item.parents:
                should_have_truth=match.ruleset.calc_truth(node,ref,tgt,
                    extrapolate=1,bias=0,exclude_links=[item] )
                truth=tgt.get_info(node,'truth')
                bias=truth-should_have_truth
                prevbias=tgt.get_info(node,'bias')
                if prevbias!=bias:
                    print 'truth of {} is {} should be {} hence bias {} (before, {})'.format(node,truth, should_have_truth,bias,prevbias)
                    #print 'MAKECHANGE',tgt,node,bias
                    cevt=ChangeInfosEvt(node,tgt,bias=bias,
                                source='perceived_link_discovery')
                    self.add_sim_child(cevt)

class BiasCalcEvt(Event):
        #OBSOLETE

        #update what Actor thinks of another's biases so that they are consistent
        #with what Actor knows of other's truth values.


    def __init__(self,item,data,**kwargs):
        super(BiasCalcEvt, self).__init__(item,data,**kwargs)
        self.type='biascalc'


    def prep_do(self,match,*args,**kwargs):
        return self.bias_calc(match,self.item,self.data)

    def bias_calc(self,match, item,graph=None,sao=None,tracklist=None):
        if tracklist is None:
            tracklist=[]
        elif item in tracklist:
            return
        #print 'updating bias', item
        srceff=match.ruleset.link_effect_from_source
        tgteff=match.ruleset.link_effect_from_target
        if graph is None:
            graph=match.canvas.active_graph

        should_have_truth=match.ruleset.calc_truth(item,graph,sao,extrapolate=1,bias=0)
        truth=sao.get_info(item,'stated_truth')
        bias=truth-should_have_truth
        prevbias=graph.get_info(item,'bias')
        #print 'truth of {} is {} should be {} hence bias {} (before, {})'.format(item,truth, should_have_truth,bias,prevbias)
        if prevbias!=bias:
            evt=ChangeInfosEvt(item,sao,bias=bias,source='biascalc')
            self.add_child(evt,{0:0,2:1},priority=-1)
        tracklist.append(item)
        for l in graph.links.get(item,[]):
            logic=graph.get_info(l,'logic')
            if l.parents[0]==item:
                if srceff(truth,logic) or srceff(should_have_truth,logic):
                    self.bias_calc(l.parents[1],graph,sao,tracklist)
            elif tgteff(truth,logic) or tgteff(should_have_truth,logic):
                self.bias_calc(l.parents[0],graph,sao,tracklist)
        return
