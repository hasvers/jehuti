# -*- coding: utf-8 -*-
from gam_match_script import *



class PhaseHandler(object):
    '''Interface of EventCommander that deals with timed events
    and scripts.'''


    time=0 #internal time
    caught_new=0
    frozen=0 #blocks all executions
    def __init__(self):
        self.evt=EventCommander(user)
        self.stack=[]
        self.done=[]
        self.timeline={}
        self.calls=nx.Graph()
        pg.event.set_blocked(30)
        self.textmaker=TextMaker(self.data)

    def get_scripts(self,**kwargs):
        '''Returns all scripts that reply to a call or satisfy a given condition.'''
        scripts=[]
        if 'call' in kwargs or 'cond' in kwargs:
            if hasattr(self.data,'all_scripts()'):
                scr=self.data.all_scripts()
            else:
                scr=self.data.scripts
            if 'call' in kwargs:
                call=kwargs['call']
                for script in scr:
                    if not script.test_cond(self,call):
                        continue
                    for c in script.conds:
                        if c.typ.lower()=='call' and c.info==call:
                            scripts.append(script)
            if 'cond' in kwargs:
                #TODO
                print "Getting scripts by condition not implemented yet"
        return scripts

    def call_scripts(self,call,**kwargs):
        for script in self.get_scripts(call=call):
            self.add_phase(script)
            if kwargs.get('src',None):
                self.add_call(kwargs['src'],script)

    def add_call(self,caller,called):
        self.calls.add_edge(caller,called)

    def freeze(self):
        self.frozen=1
    def unfreeze(self):
        self.frozen=0

    def clear_phase(self):
        cleared=[]
        #for d in self.done:
            #print d,d.item,d.effects
        for e in self.stack[::-1]+self.done[::-1]:
            if e in cleared:
                continue
            self.evt.go(e,0,ephemeral=1,handle=self)#,override=True)
            cleared.append(e)
            #print [c.state for c in e.all_children() ]


    def parse_text(self,txt):
        parsed=[]
        if isinstance(txt,list) or isinstance(txt,tuple):
            #if input provided as a sequence, join the parsed texts
            return [x for t in txt for x in self.parse_text(t) ]
        elif '|' in txt:
            txt= txt.split('|')
        else:
            txt=[txt]
        while txt:
            t=txt.pop(0)
            if hasattr(t,'keys'):
                keys=t.pop('choice')
                struct=()
                for i in keys:
                    if not i in t:
                        continue
                    j=t[i]
                    newt=j+txt
                    struct+=(i,lambda n=newt:self.add_balloon(n) ),
                FuncWrapper(lambda s=struct:self.float_menu(s,pos='center',draggable=0) )
                parsed.append()
            else:
                parsed.append(t)
        return parsed

    def add_balloon(self,txt,**kwargs):
        '''Parses text and creates a script that schedules the balloon.'''
        script=Script(name='Balloon: {}'.format(txt[:10]))
        parsed=self.parse_text(txt)
        for txt in parsed:
            eff=SceneScriptEffect()
            if isinstance(txt,basestring):
                eff.typ='Text'
                eff.text=txt
                eff.actor=kwargs.get('anchor',None)
                if kwargs.get('show_name',False):
                    eff.display='On'
            else:
                raise Exception( "Add_balloon ERROR: Not implemented yet")
            script.effects.append(eff)
        self.add_phase(script)
#        wrap=FuncWrapper(lambda t=txt,k=kwargs:user.ui.make_balloon(t,**k),type='balloon',**kwargs)
#        self.add_phase(wrap)
#        self.add_phase(FuncWrapper('wait',source=wrap,priority=-1))

    def send_balloon(self,txt,**kwargs):
        '''Called only by ScriptEffect at the instant that
        the ballon must be displayed.'''
        anchor=kwargs.pop('anchor',None)
        txt=txt.strip()
        if isinstance(anchor,basestring):
            pass
        elif hasattr(anchor, 'type'):
            if anchor.type=='actor':
                if kwargs.pop('show_name',False):
                    pre= self.textmaker.actor_name(self.cast.get_info(anchor))
                    if '*' in txt:
                        pre+=' '
                        txt=txt.replace('*','')
                        if txt[-1]!='.':
                            txt+='.'
                        txt='#i#{}##'.format(txt)
                    else:
                        pre+=': '
                        txt=txt[0].capitalize()+txt[1:]
                else:
                    pre=''
                if ':' in pre and txt[0]!='"':
                    txt='"{}"'.format(txt.replace('"',''))
                txt=pre+txt
                anchor= self.cast.view.icon[anchor]

            elif anchor.type=='node':
                anchor=self.canvas.icon[anchor]
        else:
            anchor=None
        kwargs['anchor']=anchor
        kwargs.setdefault('exit_method',self.next_phase)
        user.ui.make_balloon(txt,**kwargs)


    def add_threadevt(self,tdevt):
        '''Obsolete!'''
        print 'Obsolete use of add_threadevt by',debug.caller_name()
        self.add_phase(tdevt)

    def add_phase(self,phase):
        #print '++ Adding',phase, debug.caller_name()
        if not phase in self.stack and not phase in self.done:
            self.stack.append(phase)
            phase.schedule(self)
            #self.evt.do(phase,None,1,handle=self,ephemeral=True,time=self.time)
            #print phase.states.node[1]
            self.timeline.setdefault(self.time,set([])).add((phase,phase.state) )


    def next_phase(self,**kwargs):
        #print 'Next phase', debug.caller_name(), [(s,s.state) for s in self.stack]
        kwargs['pass_block']=True
        for e in self.stack:
            if e.states.node[e.state]['waiting']==True:
                e.states.node[e.state]['started']=self.time
                #print 'yes',e,e.state,e.states.node[e.state]['started']
        self.advance_phase(**kwargs)
        #self.evt.paused=False
        #self.evt.paused=True

    def advance_phase(self,**kwargs):
        if user.paused or self.frozen:
            return 0
        thread_blocked=[]
        for e in tuple(self.stack):
            if e.states.node[e.state]['waiting']==True:
                thread_blocked.append(e)
        for e in tuple(self.stack):
            if thread_blocked and not e in thread_blocked:
                continue
            kwargs.setdefault('handle',self)
            kwargs.setdefault('time',self.time)
            kwargs.setdefault('ephemeral',True)
            kwargs.setdefault('pass_block',False)
            handled=self.evt.do(e,**kwargs)
            if handled:
                self.timeline.setdefault(self.time,set([])).add((e,e.state) )
            if not e.states.successors(e.state):
                state=e.states.node[e.state]
                if state['started']+state['duration']<self.time:
                    self.stack.remove(e)
                    self.done.append(e)

