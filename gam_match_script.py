# -*- coding: utf-8 -*-

from gam_script_base import *
from gam_match_events import*


class CFlag(Script):
    #A conversation flag is a simplified script attached to a node (possibly extensible to script attached to any item)
    dft={}
    dft.update(Script.dft)
    dft['name']='Custom'
    dft['iter']=1
    dft['defaults']=('Custom','Include','Exclude','Perceived','LinkOnly','Unlock','Starter')
    def __init__(self,item,data,**kwargs):
        self.item=item
        self.data=data
        Script.__init__(self,**kwargs)
        self.type='cflag'
        self.cond=MatchScriptCondition()
        self.effect=MatchScriptEffect()
        self.conds=[self.cond]
        self.effects=[self.effect]

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
                for k,l in dftmodes[j][0].iteritems():
                    self.cond.set_attr(k,l)
                for k,l in dftmodes[j][1].iteritems():
                    self.effect.set_attr(k,l)
                self.effects=[self.effect]
                self.conds=[self.cond]
        elif 0:#maybe a bit too harsh for slght modifs e.g. choosing target in Unlock
            self.name='Custom'

    def __repr__(self):
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
        'start':'',
        'delay':'None',
        }

    def templatelist(self,match,nodes,links,actors):
        templatelist=SceneScriptEffect.templatelist(self,match,nodes+links,actors)
        del templatelist['Pan'] #TODO: make this possible
        del templatelist['Zoom']
        del templatelist['Scene']
        templatelist.update(
            {
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
            templatelist={'Text':templatelist['Text']}
        elif not nodes:
            templatelist={'Text':templatelist['Text'],'Cast':templatelist['Cast']}
        return templatelist

    def templates(self,template=None,**kwargs):
        match=user.ui.scene
        actors=sorted(match.actors)
        nodes=sorted(match.canvas.graph.nodes,key=lambda e:e.ID)
        links = [l for n,ls in match.canvas.graph.links.iteritems() for l in ls]
        templatelist=self.templatelist(match,nodes,links,actors)
        if template is None:
            return templatelist
        elif hasattr(template,'__iter__'):
            return [templatelist[i] for i in template]
        else:
            print templatelist[template]
            return templatelist[template]

    def __repr__(self):
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
        return SceneScriptEffect.__repr__(self)

    def prep_do(self,scene,**kwargs):
        batch=kwargs.get('batch',None)
        if self.typ in ('Graph',):
            if self.evt in ('info','add'):
                infos=self.infosep(self.info)
                if self.typ == 'Graph':
                    data=match.data.actorsubgraphs[self.owner][self.subject]
                if self.evt=='info':
                    evt= ChangeInfosEvt(self.target,data,**infos )
                elif self.evt=='add':
                    evt= AddEvt(self.target,data,infos=infos,addrequired=True )
                if batch is None:
                    if not self.all_children(): #If not already prepared
                        self.add_child(evt,{1:0,2:1},priority=1)
                else:
                    batch.add_event(evt)
                    evt.parent=batch
                    batch.add_child(evt,{1:0,2:1},priority=1)
                return True
        return SceneScriptEffect.prepare_do(self,scene,**kwargs)

    def do(self,scene,**kwargs):
        if self.typ=='Action':
            dic={'claim':ClaimEvt,'explore':ExploreEvt}
            kwargs=self.infosep(self.info)
            evt=dic[self.evt]( self, self.actor, self.target,**kwargs)
            if batch is None:
                cevt=QueueEvt(evt,match.data,newbatch=True)
                eevt=AddEvt(self.target,match.data.actorsubgraphs[self.actor][self.actor] )
                self.add_child(eevt,{1:0,2:1},priority=2)
                self.add_sim_child(cevt,priority=1)
            else:
                batch.add_event(evt)
        elif self.typ =='Canvas':
            pos= match.canvas.pos[self.target]
            glide=self.info=='Glide'
            move=self.info in ('Glide','Jump')
            if self.evt=='set barycenter':
                match.set_barycenter(pos,glide=glide,move=move)
            elif self.evt=='set camera':
                user.ui.add_visual(lambda e=pos, g=glide : match.canvas.handler.center_on(e,g))
        elif self.typ in ('Graph',):
            if self.evt in ('anim','emote'):
                if self.typ == 'Graph':
                    ic=match.canvas.icon
                for j in self.info.split(';'):
                    if self.evt=='anim':
                        user.ui.add_visual(lambda e=j:ic[self.target].set_anim(e))
                    elif self.evt=='emote':
                        user.ui.add_visual(lambda e=j:ic[self.target].call_emote(e))
                    elif self.evt=='state':
                        user.ui.add_visual(lambda e=j:ic[self.target].set_state(e))
        elif self.typ=='Conversation':
            if self.evt=='set viewpoint':
                match.set_player(self.actor,0,1)
            if self.evt=='set player':
                match.set_player(self.actor)
            elif self.evt=='set controller':
                info=self.info
                if info=='AI':
                    info=AIPlayer(self.actor,match)
                elif info=='None':
                    info=None
                match.signal('set_player',self.actor)
                match.controller.__setitem__(self.actor,info)
        elif self.typ=='Interface':
            evt='{}_ui'.format(self.evt)
            match.signal(evt,self.info)
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

        templatelist= self.templatelist(match,gphinf,nodes,links, actors,(castinf,castopt))

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
                return eval(str(rep))
            return eval(str(rep)+self.cond)
        elif self.typ=='Conversation':
            test='{}'.format(self.info)
            if not test:
                return 1
            corr={'[turn]':match.turn,
                '[time_left]':match.time_left,
                '[active_player]':'"{}"'.format(match.active_player.name)}
            for i,j in corr.iteritems():
                test=test.replace(i,str(j))
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
                #if eval('{}{}'.format(self.target.val,self.cond)):
                    ##when run, update vargraph in GameState (not in GameData!)
                    #match.parent.state.vargraph.add_edge(self.target,self)
                    #return True
        return SceneScriptCondition.test(self,match,evt)

    def __repr__(self):
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