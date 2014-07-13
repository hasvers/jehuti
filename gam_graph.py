# -*- coding: utf-8 -*-
from gam_import import *
class EthosEffect(DataBit):
    eid=0
    dft={'name':'Effect',
        'res':'face',
        'val':0.,
        'target':'claimer',
        }

    def __init__(self,**kwargs):
        self.type='effect'
        DataBit.__init__(self,**kwargs)
        self.eid=EthosEffect.eid
        EthosEffect.eid+=1
    def __repr__(self):
        val=str(int(round(self.val*database['floatprecision'])))
        if val[0]!='-':
            val='+'+val
        if isinstance(self.target,basestring):
            target=self.target
        else:
            target=self.target.name
        if self.res=='prox':
            res='Emp'
        else:
            res=self.res[:4].capitalize()
        return self.name+': '+res+val+ ' ('+target+')'



class ConvFlag(object):
    dft=('val',)
    def __init__(self,value=None):
        self.val=value
    def __eq__(self,x):
        return self.val==x
    def __contains__(self,x):
        return x in self.val
    def __repr__(self):

        return str(self.val)

    def txt_export(self,keydic,txtdic,typdic,**kwargs):
        if not id(self) in keydic:
            keydic[id(self)]=len(keydic.keys() )
            typdic.setdefault(self.__class__.__name__,[]).append(keydic[id(self)])
        txt='#{}#\n ##class:{}\n "val":"{}"\n##\n'.format(keydic[id(self)],self.__class__.__name__,self.val)
        txtdic[keydic[id(self)]]= txt


class ConvTest(DataBit):
    dft=('cond','val')
    val=None
    conds=('Default',)
    def __init__(self,value='',cond='Default'):
        self.type='convtest'
        self.val=value
        self.cond=cond

    def event_check(self,evt,item,match):
        if self.cond=='Default':
            return True
        return False

class ConvNodeTest(ConvTest):
    dft=('cond','truth','val')
    val=None
    conds=('Default','Once','Alone','Link','LinkS','LinkT','Reac')
    truths=('all','+','?','-')
    def __init__(self,value='',cond='Default',truth='all'):
        self.type='convnodetest'
        self.val=value
        self.cond=cond
        self.truth=truth

    def __repr__(self):
        return self.cond+';'+self.truth+': '+self.val
    def __str__(self):
        return self.cond+' '+self.truth+': '+self.val[:10]

    def event_check(self,evt,item,match):
        check=False
        cond=self.cond

        conds=( cond=='Default',
            (cond=='Alone' and evt.item==item),
            (cond=='Link' and evt.item.type=='link'),
            (cond=='LinkS' and hasattr(evt.item,'parents') and evt.item.parents[0]==item),
            (cond=='LinkT' and hasattr(evt.item,'parents') and evt.item.parents[1]==item),
            #(cond=='Reac' and evt.item==item)
        )
        val=match.canvas.active_graph.get_info(item,'truth')
        if True in conds :
            check =True

        if check and self.truth_check(val,match.ruleset):
            return True
        return False

    def truth_check(self,val,rules):

        truth=self.truth
        if truth=='all':
            return True
        if truth =='+' and rules.truth_value(val)>0:
            return True
        if truth =='-' and rules.truth_value(val)<0:
            return True
        if truth =='?' and rules.truth_value(val)==0:
            return True
        return False

class ConvLinkTest(ConvTest):
    conds=('Default','Reac','Claim','Contest')
    struths=('all','+','?','-'),
    ttruths=('all','+','?','-'),

    def event_check(self,evt,item,match):
        cond=self.cond
        conds=( cond=='Default',
            cond=='Reac' ,#TODO
            (cond=='Claim' and 'claim' in evt.type),
            (cond=='Contest' and 'contest' in evt.type),
        )

        if True in conds :
            return True
        return False

    def __repr__(self):
        return self.cond+': '+self.val
    def __str__(self):
        return self.cond+': '+self.val[:10]

#class ConvQuote(ConvTest):
    #def __str__(self):
        #return self.cond+' '+self.truth
#class ConvScriptCall(ConvTest):
    #pass


class MatchNode(Graph.Node):
    klass_name='MatchGraph.Node'
    dft={}
    dft.update(Graph.Node.dft)
    dft['subt']=.3
    dft['truth']=.5
    dft['bias']=0
    dft['claimed']=False
    cflags=('Starter','Include','Exclude','Perceived','LinkOnly')
    dft['cflags']=[]
    dft['lastmention']=False
    dft['quotes']=[]
    dft['calls']=[]
    dft['effects']=[]

class MatchLink(Graph.Link):
    klass_name='MatchGraph.Link'
    dft={}
    dft.update(Graph.Link.dft)
    dft['subt']=.3
    dft['val']=.2
    dft['claimed']=False
    dft['quotes']=[]
    dft['calls']=[]
    patterns=database['link_patterns']
    dft['pattern']=patterns[0]

    logics=database['link_logics']
    dft['logic']=logics[0]


class MatchSubgraph(Graph.Subgraph):
    owner=None
    klass_name='MatchGraph.Subgraph'
    infotypes={
        'node':
            ('truth',
            'bias',
            'desc',
            'quotes',
            'calls',
            'cflags',
            'terr'
            ),
        'link':
            ('desc',
            'quotes',
            'calls',
            ),
        }
    rule = 'none'

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[]).append('owner')
        kwargs.setdefault('init_param',[]).append('parent')
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def __repr__(self):
        #if self.name != Graph.Subgraph.name :
            #return 'Subgraph:'+self.name +'('+str(self.parent)+')'
        return 'Sub{}('.format(self.owner)+str(self.parent)+')'

class MatchGraph(Graph):
    name='graph'
    infotypes={
        'node':(
            'name',
            'genre',
            'val',
            'subt',
            'desc',
            'quotes',
            'calls',
            'effects'),
        'link':(
            'name',
            'pattern',
            'logic',
            'val',
            'desc',
            'quotes',
            'calls',
            'subt',),

        }
    Node=MatchNode
    Link= MatchLink
    Subgraph= MatchSubgraph

    class Props(object):
        N=60
        k=.5
        grammar='Default'
        grammars=('Default','Stupid')
        size=ergonomy['default_canvas_size']
        genre_fractions=[0.5,0.3]
        dft=('N','k','grammar','size')
        def __init__(self):
            self.leading_genre=MatchGraph.Node.genres[0]
            self.subleading_genre=MatchGraph.Node.genres[1]


class Convgraph(MatchGraph.Subgraph):
    overwrite_item=False
    infotypes={
        'node':
            ('claimed','lastmention'
            ),
        'link':
            ('claimed',
            ),
        }
    def __repr__(self):
        return 'Convgraph'
