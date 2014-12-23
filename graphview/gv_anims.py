# -*- coding: utf-8 -*-
from gv_ui_basics import *
from gv_events import TimedEvent,Event
import easing


ANIM_LEN={'instant':120,
                'short':250,
                'med':500,
                'medlong':900,
                'long':1200}

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
            if anim.states.node[0]['started'] is None:
                anim.states.node[0]['started']=self.time
                #print anim,self.time
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
                    if hasattr(affected,'react'):
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
        anim.states.node[0]['started']=None
        anim.run(0)
        anim.state=1
        for affected in anim.affects:
            if hasattr(affected,'react'):
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
            self.done=False #only useful for sounds and other punctual events
        def __repr__(self):
            return 'Step {} {}'.format(self.genre,self.args)

    def schedule(self,**kwargs):
        anim=kwargs.get('anim',self.anim)
        refpos=kwargs.get('pos',kwargs.get('ref',None ))

        if refpos is None:
            if hasattr(self.item.parent,'pos') and self.item in self.item.parent.pos:
                refpos=self.item.parent.pos[self.item]
            else:
                refpos=self.item.rect.center
        else:
            refpos=array(refpos)

        self.steps={0: [self.Step('start')]}

        if 'steps' in kwargs:
            #Allows to pass a previous list of steps
            steps=list(kwargs['steps'])
        else:
            steps=[]

        if hasattr(anim,'__iter__'):
            steps+=anim
        else:
            #time=kwargs.get('time',pg.time.get_ticks())
            time=kwargs.get('delay',0)
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
            elif anim=='sound':
                length=kwargs.get('len',1200)
                vol=kwargs.get('vol',None) #volume
                val=kwargs.get('val',None) #sound name
                steps+=[(time,length,self.Step('sound',val,vol))]
            elif anim=='emote_jump':
                length=float(kwargs.get('len',2500))
                amp=kwargs.get('amp',-20)
                tmpstep=self.schedule(anim='jump',len=length/2,amp=amp,pos=refpos,hold=True)
                tmpstep+=self.schedule(anim='appear',len=length/4,hold=True)
                tmpstep+=self.schedule(anim='sound',len=1,val='jump',hold=True)
                remlen=length-length/2-length/4 #integer division problems
                return self.schedule(anim='disappear',len=remlen,delay=3*length/4,steps=tmpstep)
            elif 'oscil' in anim:
                length=kwargs.get('len',800)
                amp=kwargs.get('amp',.1)
                periods=kwargs.get('loops',2)
                typ=kwargs.get('type','sin')
                puls= periods/float(length)*2*pi
                angle=0
                st1=self.Step('osc',refpos,(typ,amp,puls,angle))
                st2=self.Step('move',refpos,(0,0),(0,0))
                steps +=[ (time,length,st1) ,(time+length,1,st2) ]
            elif anim=='roll_in':
                length=kwargs.get('len',1200)
                st=self.Step('roll_in',kwargs.get('direction',0),override=True )
                steps+=[(time,length,st)]
            elif anim=='appear_in':
                print('TODO: Animation appear_in not working yet')
                length=kwargs.get('len',1200)
                st=self.Step('appear_in',kwargs.get('direction',0),override=True )
                steps+=[(time,length,st)]
            elif anim=='blur_in':
                length=kwargs.get('len',1200)
                st=self.Step('blur_in' )
                steps+=[(time,length,st)]
            else:
                raise Exception( 'ERROR: Unrecognized animation key:',anim)

        if kwargs.get('hold',False):
            #Don't finish scheduling just yet, instead pass step list to caller
            return steps

        steps.append( (length+1,0,self.Step("stop") ))
        states=[1]
        times=[0]
        state=1
        time=0
        starting={}
        ending={}
        durs=[]
        for step in steps:
            e=step[2]
            stime=step[0]
            e.duration=step[1]
            starting[e]=stime
            ending[e]=stime+e.duration
            durs.append(e.duration)
            if stime>time:
                durs=[stime-time for d in durs]
                time=stime
                state+=1
                states.append(state)
                times.append(time)
        for i in range(len(states)):
            s=states[i]
            if i>0:
                pred=states[i-1]
            else:
                pred=0
            self.add_state(states[i],pred=pred)
            self.steps.setdefault(s,[])
            for e in starting:
                if starting[e]<=times[i] and (ending[e]==starting[e] or times[i]<ending[e]):
                    self.steps[s].append(e)
            stat=self.states.node[s]
            stat['time']=times[i]
            if i<len(states)-1:
                stat['duration']=times[i+1]-times[i]
            else:
                stat['duration']=0
            stat['started']=None #Time at which node is stated

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
        todo=[] #Additive effects
        overrides=[] #Effects that change the image itself

        #If the animations create a different image stored in the item
        if 'anim' in self.item.images:
            del self.item.images['anim']

        for step in self.steps[state]:

            #Abnormal steps
            if step is None or step.genre=='start':
                self.item.set_state('anim',True)
                return True
            if step.genre=='stop':
                self.item.rm_state('anim')
                return False

            if step.opts.get('override',None):
                overrides.append(step)
                continue

            #Prepare common arguments and easing
            t=step.args
            t1=self.states.node[state]['started']
            if t1 is None:
                t1=self.states.node[state]['started']=time
            t2=step.duration
            if t2:
                tfrac=(float(time)-t1)/t2 #time fraction
            else:
                tfrac=0

            if tfrac<0 or tfrac>1.:
                continue
            tfrac=self.easing(self.opts.get('interpol','quad'),tfrac)

            #Effect by genre
            if step.genre=='hide':
                todo.append( (0.,0.,0.,0.) )
            elif step.genre=='sound':
                if not step.done:
                    user.ui.soundmaster.play(t[0],t[1])
                    step.done=True
            elif step.genre=='color':
                todo.append( [i+float(j-i)*tfrac for i,j in zip(*t)] )
            elif step.genre=='move':
                ref=array(t[0])
                td=[]
                for i,j in zip(*t[1:]):
                    frac=i+float(j-i)*tfrac
                    if isinstance(i,float) or isinstance(j,float):
                        frac*=self.item.rect.size[len(td)]
                    td.append(int(frac))
                todo.append( ref+ td )
            elif step.genre=='osc':
                ref=array(t[0])
                td=[]
                if t[1][0]=='sin' or t[1][0]=='rot':
                    amp,puls,angle=t[1][1:]
                    if isinstance(amp,float):
                        amp*=self.item.rect.h#sum(self.rect.size*array(sin(angle),cos(angle) ))

                    if t[1][0]=='rot':
                        angle=tfrac*puls*t2
                        val=amp
                    else:
                        val= amp*sin(puls*time-t1)
                    td=array((int(val*sin(angle)),int(val*cos(angle))))
                todo.append( ref+ td )
            elif step.genre=='blur_in':
                self.item.set_state('blur')
                dft=graphic_chart['default_blur_mode']
                self.item.blur_mode=(rint(dft[0]*(1-tfrac)), )+tuple(dft[1:])
                if tfrac>.95:
                    self.item.rm_state('blur')

        #Colormod and movement
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
                    if hasattr(self.item.parent,'pos'):
                        self.item.parent.pos[self.item]=array(t)
                    else:
                        self.item.rect.center=array(t)
            except:
                pass

        #Repaint item
        self.item.set_anim_mod(anim_mod)
        self.item.set_state('anim',True,recursive=True,invisible=True)

        #Overrides (combinations may break)
        for step in overrides:
            #compute tfrac again (sad boilerplate is sad)
            t=step.args
            t1=self.states.node[state]['started']
            if t1 is None:
                t1=self.states.node[state]['started']=time
            t2=step.duration
            if t2:
                tfrac=(float(time)-t1)/t2 #time fraction
            else:
                tfrac=0
            if tfrac<0 or tfrac>1.:
                continue
            tfrac=self.easing(self.opts.get('interpol','quad'),tfrac)

            #Effects
            if step.genre=='roll_in':
                rect=self.item.image.get_rect()
                img=self.item.image.copy()
                if not self.item.per_pixel_alpha:
                    img.set_alpha(255)
                    self.item.image.fill( COLORKEY )
                else:
                    self.item.image.fill( (0,0,0,0) )
                drc=step.args[0]
                self.item.image.blit(img,(rect.w*(tfrac-1)*cos(drc),-rect.h*(tfrac-1)*sin(drc)) )
                self.item.images['anim']=self.item.image
            elif step.genre=='appear_in':
                rec=self.item.image.get_rect()
                drc=step.args[0]
                axis=array((cos(drc),-sin(drc)))
                stop=rec.center+axis * max(rec.size)/2
                start=rec.center+axis * max(rec.size)*(-1./2+tfrac)
                if max(stop-start)<2:
                    continue
                if self.item.per_pixel_alpha:
                    print self.item
                    gradients.draw_gradient(self.item.image ,start,stop,
                     (255,255,255,255),(255,255,255,0),mode=pg.BLEND_MULT )
                else:
                    gradients.draw_gradient(self.item.image ,start,stop,COLORKEY,COLORKEY)
                self.item.images['anim']=self.item.image
        if hasattr(self.item.parent,'dirty'):
            self.item.parent.dirty=1
        return True


class Anim_Item(UI_Item):
    '''Subclass of UI_Item that contains graphical items attached to
some item for the duration of an animation (e.g. particles)'''

    def __init__(self):
        pass