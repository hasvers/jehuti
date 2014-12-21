# -*- coding: utf-8 -*-
from gv_globals import *
from gv_events import TimedEvent,Event
import easing

class AnimationHandler(object):
    '''Light version of an EventCommander, dealing only with animations
    (i.e. small effects where smooth flow is more important than precise timing,
    contrary to proper TimedEvents).'''

    def __init__(self):
        self.stack=[]
        self.done=[]
        self.time=0

    def update(self,**kwargs):
        '''Call every time step.'''

        #TODO: replace the visual queue by this, and add the condition on user.evt
        #if user.evt.moving:
            #return
        if not self.stack:
            return
        #self.time+=1
        self.done=[] #TODO: think of frequency for cleaning
        self.time=pg.time.get_ticks()
        for anim in tuple(self.stack):
            st=anim.state_at_time(self.time,**kwargs)
            ready=True
            while st!= anim.state:
                if not anim.prepare((anim.state,st)):
                    ready=False
                    break
                anim.run(anim.state,time=self.time)
                try:
                    anim.state=anim.states.successors(anim.state)[0]
                except:
                    #No successor
                    self.stack.remove(anim)
                    self.done.append(anim)
                    ready=False
                    break
            if ready and not anim.run(st,time=self.time) and not anim.states.successors(st):
                self.stack.remove(anim)
                self.done.append(anim)
                #anim.item.current_anim.remove(anim)
                for affected in anim.affects:
                    affected.react(Event(anim,type='anim_stop'))

    def clear(self):
        self.stack=[]
        self.done=[]
        self.time=0

    def add_anim(self,item,anim,*args,**kwargs):
        anim=Animation(anim,item,*args,**kwargs)
        #item.current_anim.append(anim)
        #for c in item.children:
            #c.current_anim.append(anim)
        self.stack.append(anim)
        anim.prepare( (0,1))
        self.time=pg.time.get_ticks()
        anim.states.node[0]['started']=self.time
        anim.run(0)
        anim.state=1
        for affected in anim.affects:
            affected.react(Event(anim,type='anim_start'))

class Animation(TimedEvent):
    perpetual=False

    def __init__(self,anim,item,*args,**kwargs):
        TimedEvent.__init__(self)
        self.steps=[]
        self.start=0
        self.end=-1
        self.anim=anim
        self.item=item
        self.affects=kwargs.get('affects',None)
        self.schedule(**kwargs)
        self.opts=kwargs

    def __repr__(self):
        return '{} {} {}'.format(self.anim,self.state,self.item)

    class Step(object):
        '''Single animation step'''
        def __init__(self,genre,*args,**kwargs):
            self.genre=genre
            self.args=args
            self.opts=kwargs

    @property
    def has_ended(self):
        return ( self.end>0 and  pg.time.get_ticks()>self.end )

    @property
    def has_started(self):
        return ( self.start>0 and  pg.time.get_ticks()>self.start )

    def schedule(self,**kwargs):
        anim=self.anim
        refpos=array(kwargs.get('pos',kwargs.get('ref',(0,0) )))
        if not kwargs.get('append',False):
            self.steps=[ 'start' ]
        steps=[]
        if hasattr(anim,'__iter__'):
            steps+=anim
        else:
            time=kwargs.get('time',pg.time.get_ticks())
            time+=kwargs.get('delay',0)
            if anim=='hide':
                steps+=[(time,kwargs.get('len',0),self.Step('hide') )]
            elif anim=='appear':
                #print '--- appear {} {}'.format(self,time)
                length=kwargs.get('len',1200)
                st=self.Step('color',(0,0,0,0),(1,1,1,1))
                steps+=[(time,length,st)]
            elif anim=='disappear':
                length=kwargs.get('len',1200)
                st=self.Step('color',(1,1,1,1),(0,0,0,0))
                steps+=[(time,length,st)]
            elif anim=='blink':
                length=kwargs.get('len',400)
                nblinks=kwargs.get('loops',1)
                slen=length/2./nblinks
                for z in xrange(nblinks):
                    ti=time+ 2*z*slen
                    st1=self.Step('color',(1,1,1,1),(2,2,2,1))
                    st2=self.Step('color',(2,2,2,1),(1,1,1,1))
                    steps+=[(ti,slen,st1), (ti+slen,slen,st2) ]
            elif anim=='shake':
                length=kwargs.get('len',1200)
                amp=kwargs.get('amp',.4)
                nshakes=kwargs.get('loops',3)*2
                slen=length/2./nshakes
                for z in xrange(nshakes):
                    ti=time+ 2*z*slen
                    st1=self.Step('move',refpos,(0,0),(0,amp))
                    st2=self.Step('move',refpos,(0,amp),(0,0))
                    steps+=[(ti,slen,st1),(ti+slen,slen,st2)]
                    amp*=-1
            elif anim=='jump':
                length=kwargs.get('len',1200)
                amp=kwargs.get('amp',.4)
                st=self.Step('move',refpos,(0,0),(0,amp))
                steps+=[(time,length,st)]
            elif anim=='emote_jump':
                length=float(kwargs.get('len',2500))
                amp=kwargs.get('amp',-20)
                self.schedule('jump',len=length/2,amp=amp)
                self.schedule('appear',len=length/4,append=True)
                self.schedule('disappear',len=length/4+1,delay=3*length/4,append=True)
            elif 'oscil' in anim:
                length=kwargs.get('len',800)
                amp=kwargs.get('amp',.1)
                periods=kwargs.get('loops',2)
                puls= periods/float(length)*2*pi
                angle=0
                st1=self.Step('osc',refpos,('sin',amp,puls,angle))
                st2=self.Step('pos',refpos)
                steps +=[ (time,length-100,st1) ,(time+length,0,st2) ]
            else:
                print 'ERROR: Unrecognized animation key:',anim
        steps.append( (0,0,"stop" ))
        for s,step in enumerate(steps):
            self.add_state(s+1,pred=s)
            stat=self.states.node[s+1]
            stat['time']=step[0]
            stat['duration']=step[1]
            self.steps.append(step[2] )


    def prepare(self,edge,*args,**kwargs):
        if edge==(0,1):
            if self.anim=='appear':
                #Hide before it appears
                self.item.set_anim_mod((0,0,0,0))
        return TimedEvent.prepare(self,edge,*args,**kwargs)

    def easing(self,typ,frac):
        t=frac
        b,c,d=0.,1.,1.
        if typ=='quad':
            return easing.easeInOutQuad(t,b,c,d)
        return frac


    def run(self,state,**kwargs):
        time=kwargs.get('time',None)
        step=self.steps[state]
        if step is None or step=='start':
            self.item.set_state('anim',True)
            return True
        if step=='stop':
            self.item.rm_state('anim')
            return False

        todo=[]
        t=step.args
        t1=self.states.node[state]['started']
        if t1 is None:
            t1=self.states.node[state]['started']=time
        t2=self.states.node[state]['duration']
        tfrac=(float(time)-t1)/t2 #time fraction

        if tfrac<0 or tfrac>1.:
            return False
        tfrac=self.easing(self.opts.get('interpol','lin'),tfrac)

        if step.genre=='hide':
            todo.append( (0.,0.,0.,0.) )
        elif step.genre=='color':
            todo.append( [i+float(j-i)*tfrac for i,j in zip(*t)] )
        elif step.genre=='move':
            ref=array(t[0])
            td=[]
            for i,j in zip(*t[1:]):
                frac=i+float(j-i)*tfrac
                if isinstance(i,float):
                    frac*=self.item.rect.size[len(td)]
                td.append(int(frac))
            todo.append( ref+ td )
        elif step.genre=='osc':
            if t[0]=='sin':
                amp,puls,angle=t[1:]
                if isinstance(amp,float):
                    amp*=self.item.rect.h#sum(self.rect.size*array(sin(angle),cos(angle) ))

                val= amp*sin(puls*time-t1)
                td=array((int(val*sin(angle)),int(val*cos(angle))))
            todo.append( ref+ td )

        if hasattr(self.item,'alpha'):
            albase=self.item.alpha/255.
        else:
            albase=1.
        anim_mod=array((1.,1.,1.,albase))
        for t in todo:
            #if self.item.special_anim(t):
                #continue
            try:
                if len(t)==4:
                    # Color
                    anim_mod*=array(t,dtype=float)
                elif len(t)==2:
                    #Movement
                    self.item.rect.center=array(t)
            except:
                pass

        self.item.set_anim_mod(anim_mod)
        self.item.set_state('anim',True)
        return True