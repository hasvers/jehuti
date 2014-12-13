# -*- coding: utf-8 -*-
from gam_text import*



class FuncWrapper(object):
    #For all queues of things that are not real events (e.g. match phases)
    delay=None
    method=None
    item=None
    source=None
    priority=0

    def __init__(self,item,*args,**kwargs):
        self.type=''
        self.item=item
        for i,j in tuple(kwargs.iteritems()):
            if hasattr(self,i):
                setattr(self,i,j)
                kwargs.pop(i)
        self.args=args
        self.kwargs=kwargs

    def run(self):
        if self.method:
            return self.method(self.item,*self.args,**self.kwargs)
        self.item(*self.args)

    def __eq__(self,x): #Potentially dangerous
        return self.item==x

    def __repr__(self):
        return 'Wrapper {}: {} {}'.format(self.type, self.item,self.priority)



class Script(TimedEvent):
    lastid=0
    dft={'name':'',
        'conds':[],
        'logic':'',
        'effects':[],
        'iter':'always'
        }

    #For scripted conversation bouts and effects

    def __init__(self,**kwargs):
        self.type=kwargs['type']='script'
        self.runs=0
        if not 'name' in kwargs:
            kwargs['name']='Script{}'.format(Script.lastid)
            Script.lastid+=1
        DataBit.__init__(self,**kwargs)
        TimedEvent.__init__(self,**kwargs)

    def __repr__(self):
        return 'Script:'+self.name

    def test_cond(self,scene,evt=None): #TODO: add logic i,e, cond1 && cond2 || cond3
        handled=0
        if  True in [c.attach_to_event for c in self.conds] and (evt is None or not 'batch' in evt.type):
            return 0
        for c in self.conds:
            if c.test(scene,evt):
                handled+=1
        return handled==len(self.conds)

    def prepare(self,edge,*args,**kwargs):
        if not (self.iter =='always' or self.runs<self.iter):
            return False

        if edge==(0,1):
            self.schedule(args[0])
        return TimedEvent.prepare(self,edge,*args,**kwargs)

    def run(self,state,*args,**kwargs):
        if state==1:# not self.states.successors(state):
            #TODO:
            #decide whether I should increment runs when script has finished running
            #or when it starts
            self.runs+=1
        return TimedEvent.run(self,state,*args,**kwargs)

    def run_old(self,batch=None):
        if self.iter =='always' or self.runs<self.iter:
            self.runs+=1
            if not True in [c.attach_to_event for c in self.conds]:
                batch =None
            for e in self.effects:
                e.run(batch)

    def schedule(self,scene):
        '''Run through effects to make a timed schedule
        (i.e. bind states of children events to states of script).'''
        states=[1]
        times=[0]
        state=1
        time=0
        starting={}
        startstate={}
        ending={}
        durs=[]
        #Effects with absolute timing
        #(mostly visual/spatial effects)
        for e in self.effects:
            e.prepare((0,1),scene)
            self.states.node[0]['children_states'][e]=0
            if e.start!='phase':
                starting[e]=e.start
                ending[e]=e.start+e.duration
                durs.append(ending[e])
                startstate[e]=state
        #Effects with sequential timing
        for e in self.effects:
            if e.start!='phase':
                continue
            starting[e]=time
            ending[e]=time+e.duration
            startstate[e]=state
            durs.append(e.duration)
            if e.wait=='On' or e.block_thread:
                durs=[d-e.duration for d in durs]
                time+=e.duration
                state+=1
                states.append(state)
                times.append(time)
        states.append(state+1)
        times.append(time+max(0,max(durs)))
        eff=self.effects[:]
        for i in range(len(states)):
            if i>0:
                pred=states[i-1]
            else:
                pred=None
            self.add_state(states[i],pred=pred)
            stat=self.states.node[states[i]]
            stat['waiting']=0
            for e in tuple(eff):
                if starting[e]<=times[i]<ending[e] and startstate[e]==states[i]:
                    stat['children_states'][e]=1
                elif ending[e]<=times[i] and startstate[e]<=states[i]:
                    stat['children_states'][e]=2
                    eff.remove(e)
                    if e.block_thread:
                        stat['waiting']=1
                else:
                    stat['children_states'][e]=0

            stat['time']=times[i]
            if i<len(states)-1:
                stat['duration']=times[i+1]-times[i]
            else:
                stat['duration']=0
            stat['started']=None #Time at which node is stated
        print self.states.node


class SceneScriptEffect(TimedEvent):
    dft={'name':'Effect',
        'actor':None,
        'source':None,
        'target':None,
        'evt':None,
        'text':'',
        'display':'Off',
        'typ':'Text',
        'info':'',
        'start':'phase',
        'wait':'None',
        'delay':'None',
        'duration':0
        }

    def __init__(self,**kwargs):
        self.type=kwargs['type']='scripteffect'
        DataBit.__init__(self,**kwargs)
        TimedEvent.__init__(self,**kwargs)
        self.add_state(2,pred=1)
        self.block_thread=kwargs.get('block_thread',0)

    def templatelist(self,scene,items,actors):
        if items is None:
            items=scene.data.sprites
        templatelist={
                        'Text':(
                ('actor','arrowsel',{'values':('Narrator','Down','Up')+tuple(actors)}),
                ('display','arrowsel',{'values':('On','Off'),'legend':'    Display name:'}),
                ('text','input',{'width':200,'height':200,'maxlines':None}) ),
                        'Python':(
                ('info','arrowsel',{'values':('eval','exec')}),
                ('text','input',{'width':200,'height':200,'maxlines':None}) ),
                        'Fade':(
                ('source','array',{'val':(0,0,0,0),'length':4,'width':200, 'charlimit':3,'allchars':'num','charlist':(),'typecast':int}),
                ('target','array',{'val':(0,0,0,255),'length':4,'width':200, 'charlimit':3,'allchars':'num','charlist':(),'typecast':int}),
                ('duration','input',{'val':10,'legend':'Duration'}),
                ('start','input',{'val':0,'legend':'Start'}),
                ('wait','arrowsel',{'values':('Off','On'),'legend':'Wait'}),
                    ),
                        'Pan':(
                ('target','array',{'val':(0,0),'length':2, 'charlimit':5,'allchars':'relnum','charlist':(),'typecast':int}),
                ('duration','input',{'val':10,'legend':'Duration'}),
                ('start','input',{'val':0,'legend':'Start'}),
                ('wait','arrowsel',{'values':('Off','On'),'legend':'Wait'}),
                    ),
                        'Zoom':(
                ('target','drag',{'val':1,'minval':0.1,'maxval':2.}),
                ('duration','input',{'val':10,'legend':'Duration'}),
                ('start','input',{'val':0,'legend':'Start'}),
                ('wait','arrowsel',{'values':('Off','On'),'legend':'Wait'}),
                    ),
                        'Sound':(
                ('target','input',{'val':10,'legend':'Name'}),
                ('info','drag',{'val':1,'minval':0.1,'maxval':1.,'legend':'Volume'}),
                ('text','arrowsel',{'values':('Start','Loop','Stop'),'legend':'Mode'}),
                ('delay','drag',{'val':1,'minval':0,'maxval':3000,'legend':'Fade (ms)'}),
                            ),
                        'Call':(
                ('info', 'input',{'val':''}),
                            )
                    }
        if items:
            templatelist.update({
                        'Scene':(
                ('target','extsel',{'val':items[0],'values':items,'selsource':scene}),
                ('evt','arrowsel',{'values': ('info','add','anim','emote','state')  }),
                ('info','input'),
                ),
                        'Move':(
                ('evt','extsel',{'val':None,'values':items,
                        'selsource':scene.data,'evttype':'move','seltype':'event'}),
                ('duration','input',{'val':10, 'legend':'Duration'}),
                ('start','input',{'val':0,'legend':'Start'}),
                ('wait','arrowsel',{'values':('Off','On'),'legend':'Wait'}),
                    ),
                })
        if actors:
            templatelist.update({
                'Cast':(
                ('target','arrowsel',{'values':actors+['all']}),
                ('evt','arrowsel',{'values': ('info','anim','emote','state','hud')  }),
                ('info','input',{} ),
                ),})

        #TODO: find a clean way to access game properties
        try:
            game=user.ui.game_ui.game.data
        except:
            game=scene.data.parent

        if game:
            variables=game.variables
            selfname=scene.data.filename()#name+database['{}_ext'.format(scene.data.datatype) ]
            links=game.links(selfname)
            calls=['title','END',]
            for c in links:
                if c.genre !='call':
                    continue
                for p in c.parents:
                    if p.data!=selfname:
                        calls.append(p.data)
            temps={'save': ( ('info','input',{'legend':'Name'}) , )}
            if calls:
                transitions=('None','Fade','XFade')
                transitions+=tuple(olistdir(database['image_path']+'splash/'))
                temps.update( {
                    'call':( ('target','arrowsel',{'values':calls,'width':200}) ,
                         ('info','arrowsel',{'legend':'Transition','values':transitions }),) })
            if variables:
                temps.update( {
                    'variable':( ('target','input',{'width':200}),
                         ('info','input',{'width':200,'height':200}),) })
            templatelist['Game']=(
                ('evt','arrowsel',{'values': ('call','variable','save')  ,'remake':True}),
                ) +temps.get(self.evt,())
        return templatelist


    def templates(self,template=None,**kwargs):
        scene=user.ui.scene
        actors=sorted(scene.cast.actors)
        templatelist=self.templatelist(scene,scene.data.sprites,actors)
        if template is None:
            return templatelist
        elif hasattr(template,'__iter__'):
            return [templatelist[i] for i in template]
        else:
            return templatelist[template]

    def infosep(self,info):
        infos=[]
        for inf in info.split(';'):
            if not inf:
                continue
            att,val=inf.split(':')
            att.strip()
            val.strip()
            try:
                val=eval(val)
            except:
                pass
            infos.append( (att,val) )
        return dict(infos)

    def prepare(self,edge,scene,**kwargs):
        if edge==(0,1):
            return self.prep_do(scene,**kwargs)
        return True

    def run(self,state,scene,**kwargs):
        if state==1:
            return self.do(scene,**kwargs)
        return True

    def prep_do(self,scene,**kwargs):
        if self.typ=='Text':
            self.block_thread=1
        elif self.typ=='Call':
            called=scene.get_scripts(call=self.info )
            for c in called:
                c.prepare((0,1),scene)
                laststate= [n for n in c.states.nodes() if
                     not c.states.successors(n)][0]
                scene.evt.data.bind( (self,c), {(self,c):[ (0,0),(1,laststate) ] } )
                #self.add_child(c,states={2:1,0:c.state},priority=-1)
        elif self.typ in ('Move','Pan','Fade','Zoom'):
            if self.all_children():
                #Already prepared
                return True
            self.duration=float(self.duration)
            if self.start=='phase':
                start=None
            else:
                self.start=start=float(self.start)
            if self.typ=='Move':
                tdevt=ThreadMoveEvt(self.evt.item,self.evt.graph,self.evt.pos,duration=self.duration)
            elif self.typ=='Fade':
                tdevt=FadeEvt(self.source,self.target,duration=self.duration)
            elif self.typ=='Pan':
                tdevt=PanEvt(scene.data,self.target,duration=self.duration)
            elif self.typ=='Zoom':
                tdevt=ZoomEvt(scene.data,self.target,duration=self.duration)
            self.add_sim_child(tdevt)
        elif self.typ in ('Cast','Scene') :
            if self.all_children():
                #Already prepared
                return True
            if self.evt in ('info','add'):
                infos=self.infosep(self.info)
                if self.typ=='Scene':
                    data=scene.data
                elif self.typ=='Cast':
                    data=scene.cast.data
                if self.evt=='info':
                    evt= ChangeInfosEvt(self.target,data,**infos )
                elif self.evt=='add':
                    evt= AddEvt(self.target,data,infos=infos )
                self.add_child(evt,{1:0,2:1},priority=1)
        return True


    def do(self,scene,**kwargs):
        if self.typ=='Text':
            name=False
            if self.display=='On':
                name=True
            for txt in self.text.split("|"):
                scene.add_balloon(user.ui.game_ui.game.replace_variables(txt),
                    anchor= self.actor,show_name=name)
        elif self.typ=='Python':
            if self.info=='exec':
                #TODO
                pass
                #exec(self.text)
            elif self.info=='eval':
                try:
                    scene.add_balloon(str(eval(
                        user.ui.game_ui.game.replace_variables(self.text))))
                except Exception as e:
                    print e
        elif self.typ in ('Cast','Scene') :
            if self.evt in ('anim','emote','state'):
                if self.typ=='Scene':
                    ic=scene.view.icon
                elif self.typ=='Cast':
                    ic=scene.cast.view.icon
                if self.target=='all':
                    targets=scene.cast.actors
                else:
                    targets=[self.target]
                for target in targets:
                    for j in self.info.split('|'):
                        k=j.split('=')[0].strip()
                        try:
                            opts=j.split('=')[1]
                        except:
                            opts={}
                        if opts:
                            opts={o.split(':')[0].strip():o.split(':')[1].strip() for o in opts.split(',')}
                        if self.evt=='anim':
                            phase=FuncWrapper(lambda e=k,icon=ic[target],op=opts:icon.set_anim(e,**op),
                                type='visual_{}'.format(k))
                        elif self.evt=='emote':
                            phase=FuncWrapper(lambda e=k,icon=ic[target],op=opts:icon.call_emote(e,**op),
                                type='visual_emote')
                        elif self.evt=='state':
                            if k[0]=='-':
                                func=ic[target].rm_state
                                k=k[1:]
                            else:
                                if k[0]=='+':
                                    k=k[1:]
                                func=ic[target].set_state
                            phase=FuncWrapper(lambda e=k,f=func,op=opts:f(e,**op),
                                type='visual_state')
                        phase.run()
            elif self.evt=='hud':
                if self.target=='all':
                    targets=scene.cast.actors
                else:
                    targets=[self.target]
                info = self.info.split()[0]
                margs=self.info.split()[1:]
                for target in targets:
                    phase=FuncWrapper(lambda t=target:scene.signal('{}_hud'.format(info),
                        t,*margs,affects=(scene.cast.data, )))
                    scene.add_phase(phase)
                phase.run()

        elif self.typ=='Game':
            if self.evt =='call':
                tdevt=None
                if self.info=='Fade':
                    surf=None
                elif self.info !='None':
                    if self.info=='XFade':
                        surf=scene.parent.screen.copy()
                    else:
                        try:
                            surf=image_load(database['image_path']+'splash/{}'.format(self.info) )
                            surf=pg.transform.smoothscale(surf,scene.parent.screen.get_rect().size)
                        except:
                            surf=None
                if self.info!='None':
                    tdevt=FadeEvt((0,0,0,0),(0,0,0,365),surface=surf, duration=ergonomy['transition_time']/2)
                    tdevt.block_thread=1
                    scene.add_phase(FuncWrapper(tdevt,type='fade',method=scene.add_threadevt, source=src,priority=-1))
                    #scene.add_phase(FuncWrapper('wait',source=tdevt),method=scene.add_phase)
                if not user.ui.editor_ui:
                    phase=FuncWrapper(lambda t=self.target,f=tdevt:user.ui.game_ui.goto(t,splash=f),
                        type='call',source=src,priority=-1)
                else:
                    phase= FuncWrapper(lambda t=self.target:scene.return_to_editor(),
                         type='call',source=src,priority=-1)
                scene.add_phase(phase)
                phase=FuncWrapper(scene.freeze )

            elif self.evt=='variable':
                try:
                    evt=user.ui.game_ui.game.set_variable
                    if batch is None:
                        phase=FuncWrapper(evt,self.target,self.info,type='game_var',
                            source=src,priority=-1)
                    else:
                        phase=FuncWrapper(lambda t=self.target,i=self.info,b=batch:evt(t,i,batch=b),
                            type='game_var',source=src,priority=-1)
                except Exception as e:
                    print e

            elif self.evt=='save':
                if not user.ui.editor_ui:
                    phase= FuncWrapper(user.ui.game_ui.game.save_state,self.info,type='save')
        elif self.typ=='Sound':
            if 'Stop' in self.text:
                user.ui.soundmaster.stop(self.target,fadeout=f)
            else:
                if 'Start' in self.text:
                    loops=0
                elif 'Loop'in self.text :
                    loops=-1
                user.ui.soundmaster.play(self.target,float(self.info),
                    loop=loops,fadein=int(self.delay))
        return True

    def __repr__(self):
        #base = self.name+' '+self.typ
        base=self.typ
        if self.typ=='Text':
            if self.actor:
                return base +' {}: '.format(self.actor)+self.text[:50]
            else:
                return base +': '+self.text[:50]

        elif self.typ in  ('Cast','Scene'):
            return base +': {} {} {}'.format(self.evt,self.target,self.info)
        elif self.typ =='Game':
            if self.evt=='call':
                return base+': {} {}'.format(self.evt,self.target)
            else:
                return base+': {} {} {}'.format(self.evt, self.target,self.info)
        elif self.typ=='Move':
            return '{} T={}-{}'.format(self.evt,self.start, self.info)
        elif self.typ=='Fade':
            return base+'{}->{} T={}-{}'.format(tuple(self.source),tuple(self.target),self.start, self.info)
        elif self.typ=='Pan' :
            return base+'{} {}-T={}'.format(tuple(self.target),self.start, self.info)
        elif self.typ=='Zoom':
            return base+'{} {}-T={}'.format(self.target,self.start, self.info)
        elif self.typ=='Sound':
            return base +': {} {}'.format(self.text,self.info)
        elif self.typ=='Python':
            return base +': {} {}'.format(self.info, self.text[:30])
        return base


class SceneScriptCondition(DataBit):
    dft={'name':'Cond',
        'actor':None,
        'target':None,
        'evt':None,
        'owner':None,
        'subject':None,
        'typ':'Call',
        'info':'',
        'cond':'',
        'key':'',
        }
    attach_to_event=0


    def __init__(self,**kwargs):
        self.type='scriptcond'
        DataBit.__init__(self,**kwargs)

    def __repr__(self):
        base = self.name+' '+self.typ
        if self.typ=='Event':
            return base+': {} {}'.format(self.evt,self.info)
        if self.typ in  ('Scene', 'Cast'):
            return base +': {} {} {}'.format(self.target,self.info,self.cond)
        elif self.typ=='Call':
            return base + ': {}'.format(self.info)
        elif self.typ=='Python':
            return base +': {} '.format(self.info[:30])
        elif self.typ=='Game':
            return base +': {} {} {}'.format(self.evt, self.target, self.cond)
        return self.name

    def set_attr(self,i,j):
        if self.evt in ('Change','Difference') or self.typ=='Event':
            self.attach_to_event=True
        else:
            self.attach_to_event=False
        DataBit.set_attr(self,i,j)

    def templatelist(self,scene,items=None, actors=None,castuple=None):
        templatelist={
            'Call':(
                ('info','input',{'val':self.name, 'width':200}), ),
                        'Python':(
                ('info','input',{'width':200,'height':200,'maxlines':None}), ),}
        if items:
            inf=[i for i in items[0].dft if hasattr(items[0],i)]
            templatelist.update(
            {
            'Scene':(
                ('target','extsel',{'val':items[0],'values':items,'selsource':scene}),
                ('info','arrowsel',{'values': inf }),
                ('cond','input',{'legend':'Condition'}),
                ('evt', 'arrowsel',{'values':('State','Change','Difference')})
                ),
            })
        if actors:
            castinf,castopt=castuple
            templatelist.update(
            {
            'Cast':(
                ('target','arrowsel',{'values':actors}),
                ('info','arrowsel',{'values': castinf }),
                )+castopt+(
                ('cond','input',{'legend':'Condition'}),
                ('evt', 'arrowsel',{'values':('State','Change','Difference')})
                ),
            'Event':( ('actor','arrowsel',{'values':actors}),
                ('evt','arrowsel',{'values':('Speech act',)}),
                ('info','input'),
                ),
            })
        if  scene.data.parent:
            game=scene.data.parent
            variables=game.variables
            templatelist['Game']=(
                ('evt','arrowsel',{'values': ('variable',)  }),
                ('target','arrowsel',{'values': variables ,'width':200 }),
                ('cond','input'),
                )
        return templatelist

    def templates(self,template=None,**kwargs):
        scene=kwargs.get('handler',user.ui.scene)
        actors=scene.cast.actors
        items=scene.data.sprites
        #Cast
        if actors:
            tgt=kwargs.get('target',self.target)
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
                            keyget=( 'key','extsel',{'val':items[0],'values':items,'selsource':scene})
                    except:
                        pass
                if keyget is None and hasattr(inf,'__iter__'):
                    keyget=( 'key','input',{'legend':'Key'})
                if keyget:
                    castopt+=keyget,
            templatelist= self.templatelist(scene,items, actors,(castinf,castopt))
        else:
            templatelist= self.templatelist(scene,items)

        if template is None:
            return templatelist
        else:
            return templatelist[template]


    def test(self,scene,evt=None):
        if self.typ=='Python':
            txt=user.ui.game_ui.game.replace_variables(self.info)
            try:
                return eval(txt)
            except Exception as e:
                print e
        if self.typ in ('Scene','Cast'):
            if self.typ == 'Scene':
                data=scene.data
            elif self.typ=='Cast':
                data=scene.cast.data
            if not data.contains(self.target):
                return False
            elif not self.cond:
                return True
            if self.evt=='State':
                info =data.get_info(self.target)
                if not self.info in info:
                    return False
                info=info[self.info]
            else:
                if evt is None or not hasattr(evt,'infos') or not self.info in evt.infos:
                    return False
                print 'Change', evt.item, self.info, evt.infos
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
            return eval(str(rep)+self.cond)
        elif self.typ=='Event' and not evt is None:
            if 'batch' in evt.type:
                evts=evt.events
            else:
                evts=[evt]
            for e in evts:
                if self.evt=='Speech act' and 'polite' in e.type and not 'queue' in e.type:
                    if eval('"{}"'.format(e.disc_type) +self.info):
                        return True
        elif self.typ=='Game':
            if self.evt=='variable':
                if eval(user.ui.game_ui.game.replace_variables('{}{}'.format(self.target.val,self.cond))):
                    #when run, update vargraph in GameState (not in GameData!)
                    scene.parent.state.vargraph.add_edge(self.target,self)
                    return True
        return False
