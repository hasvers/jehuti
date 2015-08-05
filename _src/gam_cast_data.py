# -*- coding: utf-8 -*-

from gam_import import *
from gam_graph import *

class Talent(DataBit):
    eid=0
    dft={'name':'Talent',
        }
    dft.update({i:0. for i in MatchGraph.Node.genres})

    def __init__(self,**kwargs):
        self.type='talent'
        DataBit.__init__(self,**kwargs)
        self.eid=Talent.eid
        Talent.eid+=1
    def __repr__(self):
        return self.name.encode('ascii','replace')+' '.join(
            ['{} {},'.format(i,getattr(self,i))
            for i in MatchGraph.Node.genres if getattr(self,i) ])
    def __str__(self):
        return self.name #+ str(id(self))

class ActorReact(DataBit):
    dft={'agree':'all','emotion':'all','event':'None','text':''}
    #val=None
    agrees=('all','+','?','-')
    emotions=('all','+','?','-','!') #'!' is for shocked i.e. high activity
    events=('None','Discovery','Concede','Dispute')
    #maybe replace offended/pleased/appeased by pleased ?pleased !pleased and make symbol ?! into separate condition
    # to shorten the list

    def __init__(self,**kwargs):
        self.type='actreac'
        DataBit.__init__(self,**kwargs)

    def __str__(self):
        return self.cond+';'+self.text

    def test_cond(self,ag,mode='Agree'):
        c=self.cond
        if ag>0 and c ==mode:
            return 1
        if ag==0 and c =='?'+mode:
            return 1
        if ag<0 and c =='!'+mode:
            return 1
        return 0


class Actor(DataItem):
    ActID=0

    dft_attr={'perc':.5,
        'agil':.5,
        'subt':.5
        }
    dft_res={'face':.5,
        'terr':.5
        }
    dft_prop={'name':'Actor',
        'prof':[],
        'portrait':database['default_portrait'],
        'color':(0,0,0,255),
        'control':'human',
        'status':'Unknown',
        'react':[],
        'patterns':database['link_patterns'],
        }

    dft_names={
        'perc':'Perception',
        'agil':'Agility',
        'subt':'Subtlety',
        'face':'Face',
        'terr':'Territory',
        'name':'Name',
        'prof':'Proficiencies',
        'status':'Status',
        'prox':'Proximity',
        'react':'Reactions',
        'control':'Controller',
        }

    dft={}

    def __init__(self,**kwargs):
        Actor.ActID+=1
        #self.prox={} #stored proximity to other actors
        for dfti in (self.dft_attr,self.dft_res,self.dft_prop):
            self.dft.update(dfti)
        self.dft['color']=graphic_chart['player_colors'][Actor.ActID%len (graphic_chart['player_colors'])]
        self.type='actor'
        DataItem.__init__(self,**kwargs)
        self.actor_id='Act'+self.name


    def __repr__(self):
        return unicode(self.name).encode('ascii','ignore')

    def __str__(self):
        return self.name

class CastData(Data):
    overwrite_item=True
    datatype='cast'
    name='dft_cast'
    infotypes={
        'actor':(),
        }

    def __init__(self,*args,**kwargs):
        self.infotypes['actor']=tuple(i for i in Actor().default_infos.keys())
        super(CastData, self).__init__(*args,**kwargs)
        self.prox={}#DataMat(self,0.)

    def get_info(self,item,info_type=None,**kwargs):
        #Hijack info read to add proximity information if available
        if info_type=='prox' and item.trueID in self.prox:
            return self.prox[item.trueID]
        info=Data.get_info(self,item,info_type,**kwargs)
        if info_type==None:
            prox=self.get_info(item,'prox',**kwargs)
            info['prox']=prox
        return info

    def set_info(self,item,ityp,val,**kwargs):
        if ityp=='prox' and item.trueID in self.prox:
            self.prox[item.trueID]=val
            return True
        return Data.set_info(self,item,ityp,val,**kwargs)


    def make_prox(self,actor=None,other=None):
        if not actor:
            for actor in self.actors:
                self.make_prox(actor,other)
            return

        #baseprox=actor.prox #Recover proximity stored in the actor himself (pickle)
        baseprox={}
        ainf=self.get_info(actor)
        self.prox.setdefault(actor.trueID,{})
        others=[other]
        if not other:
            others = self.actors
        for other in others:
            if other != actor:
                oinf = self.get_info(other)
                val=.5
                #soth=unicode(other)
                #if soth in baseprox: #USEFUL FOR SAVE/LOAD INDIVIDUAL ACTOR
                    #val =baseprox[soth]
                    #del baseprox[soth]
                #if other in baseprox:
                    #val=baseprox[other]
                self.prox[actor.trueID][other.trueID]=val#self.rules.init_prox(ainf,oinf)

                #othprox= other.prox
                val=.5
                #sact=unicode(actor)
                #if sact in othprox: #USEFUL FOR SAVE/LOAD INDIVIDUAL ACTOR
                    #val =othprox[sact]
                    #del othprox[sact]
                #if actor in othprox:
                    #val=othprox[actor]
                self.prox[other.trueID][actor.trueID]=val
                #pr=DataDict(self)
                #pr.update(self.prox[other])
                #self.set_info(other,'prox',pr,update=True)
        #pr=DataDict(self)
        #pr.update(self.prox[actor])
        #self.set_info(actor,'prox',pr,update=True)

    def add(self,actor,*args,**kwargs):
        handled = super(CastData, self).add(actor,*args,**kwargs)
        if not handled:
            return False
        self.make_prox(actor)
        #for act in self.actors:
            #if act!= actor:
                #self.make_prox(act,actor)
        return True

    def remove(self,actor):
        for oth,info in self.infos.iteritems():
            if actor.trueID in info['prox']:
                del info['prox'][actor.trueID]
        return super(CastData, self).remove(actor)

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['prox']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

class LocCastData(CastData):
    overwrite_item=False
    transparent=True
    infotypes={}
    infotypes.update(CastData.infotypes)
    infotypes['actor']+=('exporter',)

class CastState(Data):

    #evolving state during a match
    overwrite_item=False
    name='dft_caststate'
    infotypes={
        'actor':('face','terr','teri','prox','path','transcript','effects'), #teri is invested terr
        }
    transparent=True

    def __init__(self,*args,**kwargs):
        Data.__init__(self,*args,**kwargs)

        if self.rule :
            self.import_from_parent()
