# -*- coding: utf-8 -*-
from gam_graph import *
from gam_canvasicons import *



class FlowLink(Link):
    genres=('Reveal','Unlock','Lock','Claim')

    def __init__(self,parents,**kwargs):
        Link.__init__(self,parents,**kwargs)
        self.type ='link'

    def dft_modes(self,owner):
        '''Templates for script conditions and effects created
        by this links'''
        item,target=self.parents
        addeff={'typ':'Graph','target':target,'owner':owner,'subject':owner,
                        'evt':'add','info':''}
        dftmodes={
            'Include':[{'typ':'Conversation','info':'1'},addeff],
            'Reveal':[{'typ':'Graph','target':item,'owner':owner,'subject':owner,
                            'evt':'State','info':'claimed','cond':''},addeff],
            'Starter':[{'typ':'Conversation','info':'1'},
                {'typ':'Action','target':item,'actor':owner,
                        'evt':'claim','info':'cost:0'}]
            }
        return dftmodes

class FlowGraph(Graph):
    name='flowgraph'
    infotypes={
        'node':('val','scripts'),
        'link':(
            'genre',
            'val'),

        }
    Node=MatchNode
    Link= FlowLink
    Subgraph= None
    auto_import=True #automatically import nodes from underlying graph during manipulations


    def __init__(self,*args,**kwargs):
        Graph.__init__(self,*args,**kwargs)
        self.flowscript={} #Flowscript associated with a link
