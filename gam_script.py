# -*- coding: utf-8 -*-
from gam_match_script import *


class PhaseHandler(object):
    time=0 #internal time
    caught_new=0
    frozen=0
    def __init__(self):
        self.phase_queue=[] #Queue for scripts and actions that require player input
        self.threadevts=[] #Events that occur over time
        self.moving=[]
        pg.event.set_blocked(30)

    def call_scripts(self,call):
        if hasattr(self.data,'all_scripts()'):
            scr=self.data.all_scripts()
        else:
            scr=self.data.scripts
        for script in scr:
            for c in script.conds:
                if c.typ.lower()=='call' and c.info==call:
                    script.run()

    def freeze(self):
        self.frozen=1
    def unfreeze(self):
        self.frozen=0

    def clear_phase(self):
        #print self.phase_queue
        self.phase_queue=[]
        for e in self.threadevts[::-1]:
            user.evt.go(e,0,ephemeral=1)
        self.threadevts=[]

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
        wrap=FuncWrapper(lambda t=txt,k=kwargs:user.ui.make_balloon(t,**k),type='balloon',**kwargs)
        self.add_phase(wrap)
        self.add_phase(FuncWrapper('wait',source=wrap,priority=-1))

    def add_threadevt(self,tdevt):
        self.threadevts.append(tdevt)
        self.caught_new=1

    def advance_phase(self):
        if user.paused or self.frozen:
            return 0
        handled=0
        block=0
        phase_queue=self.phase_queue
        for e in self.threadevts:
            if  e in user.evt.moving:
                continue
            ehandled=0
            if e.state==0 and (e.tinit is None or self.time>=e.tinit):
                ehandled =  user.evt.do(e,None,1,handle=self,time=self.time,ephemeral=True)
            elif e.state==1 and e.tinit+e.step-1<=self.time <= e.tinit+ e.duration:
                ehandled= user.evt.do(e,None,1,handle=self,time=self.time,ephemeral=True)
            elif e.state!=2 :
                try:
                    if e.tinit+ e.duration< self.time:
                        handled=  user.evt.do(e,None,2,handle=self,ephemeral=True) or handled
                except:
                    pass
            if e.state==1 and e.block_thread==True:
                block=1
            handled=handled or ehandled
        i=0
        while i<len(phase_queue) and not block:
            if phase_queue[0] == 'wait':
                #try: #OBSOLETE WAY OF HAVING e.block_thread
                    #if self.phase_queue[0].source.state==2:
                        #self.phase_queue.pop(0)
                        #continue
                #except:
                    #pass
                break
            phase=phase_queue[i]
            if phase in self.moving:
                break
            if not hasattr(phase,'delay') or not phase.delay:
                self.moving.append(phase)
                handled =True
                if hasattr(phase,'type') and 'visual' in phase.type:
                    user.ui.add_visual(phase.item)
                else:
                    if hasattr(phase, 'run'):
                        phase.run()
                    else:
                        phase()
                j=i
                if self.frozen or not phase_queue:
                    print 'Phase queue has been cleared'
                    break
                i=phase_queue.index(phase)
                phase_queue.pop(i)
                self.moving.remove(phase)
                if hasattr(phase,'type') and 'balloon' not in phase.type :
                    while phase_queue and phase_queue[i]=='wait' and phase_queue[i].source==phase:
                        phase_queue.pop(i)
                i=j-1
            if self.caught_new:
                break
            i+=1
            #print 'DONE', phase, self.time, self.phase_queue

        if self.frozen:
            return 0

        if self.caught_new: #If the queue has been modified while it ran
            self.caught_new=0
            return self.advance_phase() or handled
        user.ui.visual_advance()
        return handled


    def next_phase(self):
        #print debug.caller_name(), [(z,id(z)) for z in self.phase_queue]
        while self.phase_queue and self.phase_queue[0]=='wait':
            self.phase_queue.remove('wait')
        return self.advance_phase()
        #print '----END'

    def add_phase(self,phase,pos=None,**kwargs):
        #print '   ADD', phase, debug.caller_name()
        if kwargs.pop('visual',False):
            self.add_phase(FuncWrapper(lambda u=user.ui,p=phase: u.add_visual(p)),pos,**kwargs)
            return
        #try:
            #print phase,'source', phase.source,'\n'
        #except:
            #print phase, 'nosource'
        if pos is None:
            pos=len(self.phase_queue)
            if hasattr(phase,'priority'):
                priority=phase.priority
            else:
                priority=kwargs.pop('priority',None)
            if hasattr(phase,'source'):
                source=phase.source
            else:
                source=kwargs.pop('source',None)
            if priority and source:
                for ppos,p in enumerate(self.phase_queue):
                    if not hasattr(p,'priority'):
                        print 'PROBLEM IN THE QUEUE',p,self.phase_queue
                    if priority=='start' and p.priority!='start':
                        pos=min(pos,ppos)
                    elif p.priority=='end':
                        pos=min(pos,ppos)
                    elif source==p: #for instance 'wait' sourced by balloons are always after the balloon
                        pos=ppos+1
                    elif hasattr(p,'delay'):
                        if p.delay>=phase.delay:
                            if p.delay>phase.delay:
                                pos=min(pos,ppos)
                            elif p.source==source:
                                if p.priority< priority:
                                    pos=min(pos,ppos)
                                else:
                                    pos=max(pos,ppos+1)
                        else:
                            pos=max(pos,ppos+1)
                while (pos<len(self.phase_queue) and hasattr(self.phase_queue[pos],'source')
                    and self.phase_queue[pos].source==self.phase_queue[max(pos-1,0)]):
                        #Do not separate a wrapper from children wrappers (that have it as source)
                        pos+=1
        self.phase_queue.insert(pos,phase)
        self.caught_new=1
