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
    def __str__(self):
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


class ConvTest(DataBit):
    '''Basic class for tests of conversation item state.'''

    dft={'cond':'Default'}
    conds=('Default',)

    def event_check(self,evt,item,match):
        if self.cond=='Default':
            return True
        return False

    def truth_check(self,val,rules,truth):
        if truth=='all':
            return True
        if truth =='+' and rules.truth_value(val)>0:
            return True
        if truth =='-' and rules.truth_value(val)<0:
            return True
        if truth =='?' and rules.truth_value(val)==0:
            return True
        return False

class ConvNodeTest(ConvTest):
    '''Basic class for tests of conversation node state.'''

    dft={'cond':'Default','truth':'all'}
    conds=('Default','Once','Alone','Link','LinkS','LinkT','Reac')
    truths=('all','+','?','-')
    def __init__(self,**kwargs):
        ConvTest.__init__(self,**kwargs)
        self.type='convnodetest'
        self.cond=cond
        self.truth=truth

    def __str__(self):
        return self.cond+' '+self.truth

    def event_check(self,evt,item,match):
        check=False
        cond=self.cond
        conds=( cond=='Default',
            cond=='Reac' and evt=='Reac')
        if hasattr(evt,'item'):
            conds+=(
                (cond=='Alone' and evt.item==item),
                (cond=='Link' and evt.item.type=='link'), )
            if hasattr(evt.item,'parents'):
                conds +=(
                    (cond=='LinkS' and  evt.item.parents[0]==item),
                    (cond=='LinkT' and evt.item.parents[1]==item),)
        if True in conds :
            check =True

        val=match.canvas.active_graph.get_info(item,'truth')
        if check and self.truth_check(val,match.ruleset,self.truth):
            return True
        return False

class ConvLinkTest(ConvTest):
    '''Basic class for tests of conversation link state.'''

    conds=('Default','Reac','Claim','Contest')
    struths=('all','+','?','-'),
    ttruths=('all','+','?','-'),
    dft={'cond':'Default','struth':'all','ttruth':'all'}

    def event_check(self,evt,item,match):
        cond=self.cond
        conds=( cond=='Default',
            cond=='Reac' and evt=='Reac',)
        if hasattr(evt,'item'):
            conds+=(
                (cond=='Claim' and 'claim' in evt.type),
                (cond=='Contest' and 'contest' in evt.type),
            )

        vals=[match.canvas.active_graph.get_info(p,'truth') for p in item.parents]
        tconds=self.truth_check(vals[0],match.ruleset,self.struth)
        tconds = tconds and self.truth_check(val[1],match.ruleset,self.ttruth)
        if True in conds and tconds :
            return True
        return False

    def __str__(self):
        return '{} {} {}'.format(self.cond,self.struth,self.ttruth)

class MatchNode(Graph.Node):
    klass_name='MatchGraph.Node'
    dft={}
    dft.update(Graph.Node.dft)
    dft['subt']=.3
    dft['truth']=.5
    dft['bias']=0
    dft['claimed']=False
    dft['cflags']=[]
    dft['lastmention']=False
    dft['scripts']=[]
    dft['effects']=[]

class MatchLink(Graph.Link):
    klass_name='MatchGraph.Link'
    dft={}
    dft.update(Graph.Link.dft)
    dft['subt']=.3
    dft['val']=.5
    dft['claimed']=False
    dft['scripts']=[]
    dft['cflags']=[]
    patterns=database['link_patterns']
    dft['pattern']=patterns[0]

    logics=database['link_logics'] #(a,b,c,d)
    dft['logic']=logics[0]



class MatchSubgraph(Graph.Subgraph):
    owner=None
    klass_name='MatchGraph.Subgraph'
    infotypes={
        'node':
            ('truth',
            'stated_truth',#Useful only for subgraph[self][other]: allows to reeval bias
            'bias',
            'uncertainty',
            'desc',
            'scripts',
            'cflags',
            'terr',
            ),
        'link':
            ('desc',
            'scripts',
            'cflags',
            'activity',
            ),
        }
    rule = 'none'

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[]).append('owner')
        kwargs.setdefault('init_param',[]).append('parent')
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def __str__(self):
        if self.name != Graph.Subgraph.name :
            return 'Sub:'+self.name# +'('+unicode(self.parent)+')'
        return 'Sub{}('.format(self.owner)+unicode(self.parent)+')'


class MatchGraph(Graph):
    name='graph'
    infotypes={
        'node':(
            'name',
            'genre',
            'val',
            'subt',
            'desc',
            'scripts',
            'cflags',
            'effects'),
        'link':(
            'name',
            'pattern',
            'logic',
            'val',
            'desc',
            'scripts',
            'cflags',
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
    def __str__(self):
        return 'Convgraph'
