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
        pg.event.set_blocked(30)


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
                    for c in script.conds:
                        if c.typ.lower()=='call' and c.info==call:
                            scripts.append(script)
            if 'cond' in kwargs:
                #TODO
                print "Getting scripts by condition not implemented yet"
        return scripts

    def call_scripts(self,call):
        for script in self.get_scripts(call=call):
            self.add_phase(script)

    def freeze(self):
        self.frozen=1
    def unfreeze(self):
        self.frozen=0

    def clear_phase(self):
        for e in self.stack[::-1]:
            self.evt.go(e,0,ephemeral=1,handle=self)

    def add_balloon(self,txt,**kwargs):
        if '|' in txt:
            for j in txt.split('|'):
                self.add_balloon(j,**kwargs)
            return
        anchor=kwargs.pop('anchor',None)
        txt=txt.strip()
        if isinstance(anchor,basestring):
            pass
        elif hasattr(anchor, 'type'):
            if anchor.type=='actor':
                if kwargs.pop('show_name',False):
                    pre= TextMaker(self.data).actor_name(self.cast.get_info(anchor))
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
        kwargs['priority']='start'
        user.ui.make_balloon(txt,**kwargs)
#        wrap=FuncWrapper(lambda t=txt,k=kwargs:user.ui.make_balloon(t,**k),type='balloon',**kwargs)
#        self.add_phase(wrap)
#        self.add_phase(FuncWrapper('wait',source=wrap,priority=-1))

    def add_threadevt(self,tdevt):
        '''Obsolete!'''
        print 'Obsolete use of add_threadevt by',debug.caller_name()
        self.add_phase(tdevt)

    def add_phase(self,phase):
        self.stack.append(phase)
        self.evt.do(phase,None,1,handle=self,ephemeral=True,time=self.time)

    def next_phase(self,**kwargs):
        kwargs['repeat_only']=False
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
        for e in self.stack:
            kwargs.setdefault('handle',self)
            kwargs.setdefault('time',self.time)
            kwargs.setdefault('ephemeral',True)
            kwargs.setdefault('repeat_only',True)
            self.evt.do(e,**kwargs)

