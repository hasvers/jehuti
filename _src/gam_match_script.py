# -*- coding: utf-8 -*-

from gam_script import *
from gam_match_events import*


class CFlag(DataBit):
    '''A conversation flag is any tag that may be relevant to a node or link.'''
    dft={'val':'Include',
        'info':'',}

    defaults=['Include','Starter','Exclude','Perceived',
            'LinkOnly','Doxa','Locked']

    def __str__(self):
        return self.val

    #def __eq__(self,x):
        #if hasattr(x,'val'):
            #return self.__class__==x.__class__ and self.val==x.val
        #return self.val==x

class OldestCFlag(object):
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

class OldCFlag(Script):
    #A conversation flag is a simplified script attached to a node (possibly extensible to script attached to any item)
    dft={}
    dft.update(Script.dft)
    dft['name']='Custom'
    dft['iter']=1
    def __init__(self,item,data,**kwargs):
        self.item=item
        self.data=data
        Script.__init__(self,**kwargs)
        self.type='cflag'
        self.cond=MatchScriptCondition()
        self.effect=MatchScriptEffect()
        self.conds=[self.cond]
        self.effects=[self.effect]

    def copy(self):
        new=self.__class__(self.item,self.data,type=self.type,name=self.name)
        new.cond=self.cond.copy()
        new.effect=self.effect.copy()
        new.conds=[new.cond]
        new.effects=[new.effect]
        return new

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[]).extend(['item','data'])
        kwargs.setdefault('init_param',[]).extend(['item','data'])
        return Script.txt_export(self,keydic,txtdic,typdic,**kwargs)


    def set_attr(self,i,j):
        Script.set_attr(self,i,j)
        owner=self.data.owner
        addeff={'typ':'Graph','target':self.item,'owner':owner,'subject':owner,
                        'evt':'add','info':''}
        dftmodes={
            'Include':[{'typ':'Conversation','info':'1'},addeff],
            'Unlock':[{'typ':'Graph','target':self.item,'owner':owner,'subject':owner,
                            'evt':'State','info':'claimed','cond':''},addeff],
            'Starter':[{'typ':'Conversation','info':'1'},
                {'typ':'Action','target':self.item,'actor':owner,
                        'evt':'claim','info':'cost:0'}]
            }

        if i=='name':
            if j in dftmodes:
                print 'Setting',j,dftmodes[j]
                for k,l in dftmodes[j][0].iteritems():
                    self.cond.set_attr(k,l)
                for k,l in dftmodes[j][1].iteritems():
                    self.effect.set_attr(k,l)
                self.effects=[self.effect]
                self.conds=[self.cond]
        elif 0:#maybe a bit too harsh for slght modifs e.g. choosing target in Unlock
            self.name='Custom'

    def __str__(self):
        return self.name


#Types of scripted consequences:
#- Conversation bout
#- Canvas:
    #-Conv state change: Evttype (Explore, Claim, Declar), target (link or node),
    #-Subgraphs info change: Owner,Subject,target,infos
    #  (binomial input list transformed into kwargs, will not work for flags and quotes though)
#- Actor info change: resource type
##- Match state change: win, lose, interrupt,


class MatchScriptEffect(SceneScriptEffect):
    dft={'name':'Effect',
        'actor':None,
        'source':None,
        'target':None,
        'evt':None,
        'owner':None,
        'subject':None,
        'text':'',
        'display':'Off',
        'typ':'Text',
        'info':'',
        'wait':'Off',
        'start':'phase',
        'delay':'None',
        'duration':0
        }


    def templatelist(self,match,nodes,links,actors):
        templatelist=SceneScriptEffect.templatelist(self,match,nodes+links,actors)
        del templatelist['Pan'] #TODO: make this possible
        del templatelist['Zoom']
        del templatelist['Scene']
        templatelist.update(
            {
            #'AutoText':(('text','input'),
                #('info','input',{'legend':'Options:'}),
                #),
            'Action':( ('actor','arrowsel',{'values':actors}),
                ('target','extsel',{'val':nodes[0],'values':nodes +links,'selsource':match.canvas}),
                ('evt','arrowsel',{'values':('claim','explore','declar')}),
                ('delay','arrowsel',{'legend':'Delay:','values':('None','Own turn','Option')}),
                ('info','input',{'legend':'Options:'}),
                ('wait','arrowsel',{'values':('Off','On')}),
                ),
            'Graph':( ('owner','arrowsel',{'values':actors}),
                ('subject','arrowsel',{'values':actors}),
                ('target','extsel',{'val':nodes[0],'values':nodes +links,'selsource':match.canvas}),
                ('evt','arrowsel',{'values': ('info','add','anim','emote','state')  }),
                ('info','input'),
                ),
            'Canvas':(
                ('evt','arrowsel',{'values': ('set camera','set barycenter') }),
                ('target','extsel',{'val':nodes[0],'values':nodes ,'selsource':match.canvas}),
                ('info','arrowsel',{'values':('Glide','Jump','Still')}),
                ),
            'Conversation':(
                ('evt','arrowsel',{'values': ('set viewpoint','set active','set controller') }),
                ('actor','arrowsel',{'values':actors}),
                ('info','arrowsel',{'values': ('human','AI','None') }),
                ('wait','arrowsel',{'values':('Off','On')}),
                ),
            'Interface':(
                ('evt','arrowsel',{'values': ('show','hide','anim')}),
                ('info','input'),
                ('wait','arrowsel',{'values':('Off','On')}),
                ),
            }
        )

        if not actors:
            templatelist={'Text':templatelist['Text']}#,'AutoText':templatelist['AutoText']}
        elif not nodes:
            templatelist={'Text':templatelist['Text'],'Cast':templatelist['Cast']}
        return templatelist

    def templates(self,template=None,**kwargs):
        match=kwargs.get('scene',user.ui.scene) #TODO: remove the dependence in user.ui
        actors=sorted(match.actors)
        nodes=sorted(match.canvas.graph.nodes,key=lambda e:e.ID)
        links = [l for n,ls in match.canvas.graph.links.iteritems() for l in ls]
        templatelist=self.templatelist(match,nodes,links,actors)
        if template is None:
            return templatelist
        elif hasattr(template,'__iter__'):
            return [templatelist[i] for i in template]
        else:
            return templatelist[template]

    def __str__(self):
        base = self.name+' '+self.typ
        if self.typ=='Action':
            return base +': {} {}'.format(self.evt,self.target)
        if self.typ in  ('Graph',):
            return base +': {} {}'.format(self.evt,self.target)
        if self.typ=='Conversation':
            return  base +': {} {}'.format(self.evt,self.info)
        if self.typ=='Interface':
            return base +': {} {}'.format(self.evt,self.info)
        if self.typ=='Canvas':
            return base +': {} {}'.format(self.evt,self.target)
        #if self.typ=='AutoText':
            #return base+': {}'.format(self.text)
        return SceneScriptEffect.__repr__(self)

    def prep_do(self,scene,**kwargs):
        batch=kwargs.get('batch',None)

        #print '@@@ PREPARING',self,id(self)
        self.clear_children()
        if self.typ in ('Graph',):
            if self.evt in ('info','add'):
                infos=self.infosep(self.info)
                if self.typ == 'Graph':
                    data=scene.data.actorsubgraphs[self.owner][self.subject]
                if self.evt=='info':
                    evt= ChangeInfosEvt(self.target,data,**infos )
                elif self.evt=='add':
                    evt= AddEvt(self.target,data,infos=infos,addrequired=True )
                if batch is None:
                    self.add_child(evt,{1:0,2:1},priority=1)
                else:
                    if not True in [c.duplicate_of(evt) for c in batch.rec_events]:
                        batch.add_event(evt)
                        evt.parent=batch
                        batch.add_child(evt,{1:0,2:1},priority=1)
                #print '\n\n============\n',self,id(self),id(self.states),id(self.states.node)
                return True
        elif self.typ=='Action':
            dic={'claim':ClaimEvt,'explore':ExploreEvt}
            kwargs=self.infosep(self.info)
            evt=dic[self.evt]( self, self.actor, self.target,**kwargs)
            if batch is None:
                cevt=QueueEvt(evt,scene.data,newbatch=True)
                eevt=AddEvt(self.target,scene.data.actorgraph[self.actor] )#[self.actor]
                self.add_child(eevt,{1:0,2:1},priority=2)
                #TODO:BREAK? understand if the add event had to be on [self.actor][self.actor]
                #TODO:BREAK? despite there being an identical addevt in claim
                self.add_sim_child(cevt,priority=1)
            else:
                if not True in [c.duplicate_of(evt) for c in batch.rec_events]:
                    batch.add_event(evt)
            return True
        return SceneScriptEffect.prep_do(self,scene,**kwargs)

    def do(self,scene,**kwargs):
        if self.typ =='Canvas':
            pos= scene.canvas.pos[self.target]
            glide=self.info=='Glide'
            move=self.info in ('Glide','Jump')
            if self.evt=='set barycenter':
                scene.set_barycenter(pos,glide=glide,move=move)
            elif self.evt=='set camera':
                user.ui.add_visual(lambda e=pos, g=glide : scene.canvas.handler.center_on(e,g))
        elif self.typ in ('Graph',):
            if self.evt in ('anim','emote'):
                if self.typ == 'Graph':
                    ic=scene.canvas.icon
                for j in self.info.split(';'):
                    if self.evt=='anim':
                        user.ui.add_visual(lambda e=j:ic[self.target].set_anim(e))
                    elif self.evt=='emote':
                        user.ui.add_visual(lambda e=j:ic[self.target].call_emote(e))
                    elif self.evt=='state':
                        user.ui.add_visual(lambda e=j:ic[self.target].set_state(e))
        elif self.typ=='Conversation':
            if self.evt=='set viewpoint':
                scene.set_player(self.actor,0,1)
            if self.evt=='set player':
                scene.set_player(self.actor)
            elif self.evt=='set controller':
                info=self.info
                if info=='AI':
                    info=AIPlayer(self.actor,scene)
                elif info=='None':
                    info=None
                scene.signal('set_player',self.actor)
                scene.controller.__setitem__(self.actor,info)
        elif self.typ=='Interface':
            evt='{}_ui'.format(self.evt)
            scene.signal(evt,self.info)
        else:
            return SceneScriptEffect.do(self,scene,**kwargs)
        return True



class MatchScriptCondition(SceneScriptCondition):

    def templatelist(self,match,gphinf,nodes,links, actors,castuple):
        castinf,castopt=castuple
        templatelist={
            'Action':( ('actor','arrowsel',{'values':actors}),
                ('target','extsel',{'val':nodes[0],'values':nodes +links,'selsource':match.canvas}),
                #('target','arrowsel',{'values':nodes}),
                ('evt','arrowsel',{'values':('claim','explore','declar')})
                ),
            'Graph':( ('owner','arrowsel',{'values':actors}),
                ('subject','arrowsel',{'values':actors}),
                ('target','extsel',{'val':nodes[0],'values':nodes +links,'selsource':match.canvas}),
                ('info','arrowsel',{'values': gphinf }),
                ('cond','input',{'legend':'Condition'}),
                ('evt', 'arrowsel',{'values':('State','Change','Difference')})
                ),
            'Cast':(
                ('target','arrowsel',{'values':actors}),
                ('info','arrowsel',{'values': castinf }),
                )+castopt+(
                ('cond','input',{'legend':'Condition'}),
                ('evt', 'arrowsel',{'values':('State','Change','Difference')})
                ),
            'Conversation':(
                ('info','input'),
                ),
            'Event':( ('actor','arrowsel',{'values':actors}),
                ('evt','arrowsel',{'values':('Speech act',)}),
                ('info','input'),
                ),
            'Ethos':( ('actor','arrowsel',{'values':actors}),#TODO:delete or finish this
                ('evt','arrowsel',{'values':('speech','polite')}),
                ('info','input'),
                ),
            'Call':(
                ('info','input',{'val':self.name,'width':200}), ),
            }
        if  match.data.parent:
            game=match.data.parent
            variables=game.variables
            templatelist['Game']=(
                ('evt','arrowsel',{'values': ('variable',)  }),
                ('target','arrowsel',{'values': variables ,'width':200 }),
                ('cond','input'),
                )
        return templatelist

    def templates(self,template=None,**kwargs):
        match=user.ui.scene
        actors=match.actors
        nodes=match.canvas.graph.nodes
        links = [l for n,ls in match.canvas.graph.links.iteritems() for l in ls]

        #Cast
        tgt=kwargs.get('target',self.target)
        if actors:
            if not tgt in actors:
                tgt=actors[0]
            castinf=[i for i in tgt.dft if hasattr(tgt,i)]
            castopt=()
            if self.info in castinf:
                inf=getattr(tgt,self.info)
                keyget=None
                if hasattr(inf,'keys') and inf:
                    try:
                        if inf.keys()[0].type=='actor' :
                            keyget=( 'key','arrowsel',{'values':actors})
                        elif inf.keys()[0].type=='node' :
                            keyget=( 'key','extsel',{'val':nodes[0],'values':nodes +links,'selsource':match.canvas})
                    except:
                        pass
                if keyget is None and hasattr(inf,'__iter__'):
                    keyget=( 'key','input',{'legend':'Key'})
                if keyget:
                    castopt+=keyget,

        gphtgt=kwargs.get('target',self.target)
        if not gphtgt or not match.canvas.graph.contains(gphtgt):
            gphtgt=nodes[0]
        gphinf=[i for i in gphtgt.dft if hasattr(gphtgt,i)]

        if actors:
            templatelist= self.templatelist(match,gphinf,nodes,links, actors,(castinf,castopt))
        else:
            templatelist= self.templatelist(scene,gphinf,nodes,links)


        if template is None:
            return templatelist
        else:
            return templatelist[template]


    def test(self,match,evt=None):
        if self.typ=='Action':
            return False
        elif self.typ in ('Graph',):
            if self.typ == 'Graph':
                data=match.data.actorsubgraphs[self.owner][self.subject]
            if not data.contains(self.target):
                return False

            if self.evt=='State':
                info =data.get_info(self.target)
                if not self.info in info:
                    print 'MatchScrCond missing', data,self.target, self.info
                    return False
                info=info[self.info]
            else:
                if evt is None or not hasattr(evt,'infos') or not self.info in evt.infos:
                    return False
                #print 'Change', evt.item, self.info, evt.infos
                if evt.item!=self.target:
                    return False
                if self.evt=='Difference':
                    if evt.additive:
                        info=evt.kwargs[self.info]
                    else:
                        info=evt.sinfos(evt.state)[self.info]
                else:
                    info=evt.infos[self.info]
            #test='{}'.format(self.info)
            #for i,j in infos.iteritems() :
            if hasattr(info,'__iter__'):
                rep=info[self.key]
                if self.evt=='Difference' and not evt.additive:
                    rep-=evt.sinfos(1-evt.state)[self.info][self.key]
            else:
                rep=info
            #print rep, self.cond, eval(str(rep)+self.cond),data.name#,data.get_info(self.target)
            if not self.cond:
                return eval(unicode(rep))
            return eval(unicode(rep)+self.cond)
        elif self.typ=='Conversation':
            test='{}'.format(self.info)
            if not test:
                return 1
            corr={'[turn]':match.turn,
                '[time_left]':match.time_left,
                '[active_player]':'"{}"'.format(match.active_player.name)}
            for i,j in corr.iteritems():
                test=test.replace(i,unicode(j))
            return eval(test)
        elif self.typ=='Event' and not evt is None:
            if 'batch' in evt.type:
                evts=evt.events
            else:
                evts=[evt]
            for e in evts:
                if self.evt=='Speech act' and 'polite' in e.type and not 'queue' in e.type:
                    if eval('"{}"'.format(e.disc_type) +self.info):
                        return True
        #elif self.typ=='Game':
            #if self.evt=='variable':

        return SceneScriptCondition.test(self,match,evt)

    def __str__(self):
        base = self.name+' '+self.typ
        if self.typ in ('Conversation','Call'):
            return base +': '+self.info[:8]
        if self.typ=='Event':
            return base+': {} {}'.format(self.evt,self.info)
        if self.typ=='Action':
            return base +': {} {}'.format(self.evt,self.target)
        if self.typ in  ('Graph', 'Cast'):
            return base +': {} {} {}'.format(self.target,self.info,self.cond)
        return SceneScriptCondition.__repr__(self)



class ConvNodeScript(Script,ConvNodeTest):
    '''Script started by a ConvNodeTest'''
    dft={}
    dft.update(Script.dft)
    dft.update(ConvNodeTest.dft)
    dft["text"]=''
    def test_cond(self,scene,evt=None):
        return self.event_check(evt,self.item,scene) and MatchScript.test_cond(self,scene,evt)

    def __str__(self):
        return 'NodeScr:'+self.name

class ConvLinkScript(Script,ConvLinkTest):
    '''Script started by a ConvLinkTest'''
    dft={}
    dft.update(Script.dft)
    dft.update(ConvLinkTest.dft)
    dft["text"]=''
    def test_cond(self,scene,evt=None):
        return self.event_check(evt,self.item,scene) and MatchScript.test_cond(self,scene,evt)


    def __str__(self):
        return 'LinkScr:'+self.name