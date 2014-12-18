# -*- coding: utf-8 -*-
from gv_uibasics import *

class Animation(TimedEvent):
    perpetual=False

    def __init__(self,anim,item,*args,**kwargs):
        self.steps=[]
        self.start=0
        self.end=-1
        self.anim=anim
        self.item=item

    @property
    def has_ended(self):
        return ( self.end>0 and  pg.time.get_ticks()>self.end )

    @property
    def has_started(self):
        return ( self.start>0 and  pg.time.get_ticks()>self.start )

    def prepare_init(self,**kwargs):
        anim=self.anim
        refpos=array(kwargs.get('pos',kwargs.get('ref',(0,0) )))
        if hasattr(anim,'__iter__'):
            self.steps+=anim
        elif True :#or not self.current_anim: #TODO: Is this condition necessary?
            time=kwargs.get('time',pg.time.get_ticks())
            time+=kwargs.get('delay',0)
            if anim=='appear':
                print '--- appear {} {}'.format(self,time)
                length=kwargs.get('len',1200)
                self.steps+=[((time,length),(0,0,0,0),(1,1,1,1))]
            if anim=='disappear':
                length=kwargs.get('len',1200)
                self.steps+=[((time,length),(1,1,1,1),(0,0,0,0))]
            if anim=='blink':
                length=kwargs.get('len',400)
                nblinks=kwargs.get('loops',1)
                slen=length/2./nblinks
                #self.current_anim=[]
                for z in xrange(nblinks):
                    ti=time+ 2*z*slen
                    self.steps+=[((ti,slen),(1,1,1,1),(2,2,2,1)),
                        ((ti+slen,slen),(2,2,2,1),(1,1,1,1)) ]
            if anim=='shake':
                length=kwargs.get('len',1200)
                amp=kwargs.get('amp',.4)
                nshakes=kwargs.get('loops',3)*2
                slen=length/2./nshakes
                #self.current_anim=[]
                for z in xrange(nshakes):
                    ti=time+ 2*z*slen
                    self.steps+=[((ti,slen),refpos,(0,0),(0,amp)),
                        ((ti+slen,slen),refpos,(0,amp),(0,0))]
                    amp*=-1
            if anim=='jump':
                length=kwargs.get('len',1200)
                amp=kwargs.get('amp',.4)
                self.steps+=[((time,length),refpos,(0,0),(0,amp))]
            if anim=='emote_jump':
                length=float(kwargs.get('len',2500))
                amp=kwargs.get('amp',-20)
                self.set_anim('jump',len=length/2,amp=amp)
                self.set_anim('appear',len=length/4)
                self.set_anim('disappear',len=length/4+1,delay=3*length/4)
            if 'oscil' in anim:
                length=kwargs.get('len',800)
                amp=kwargs.get('amp',.1)
                periods=kwargs.get('loops',2)
                puls= periods/float(length)*2*pi
                angle=0
                self.steps +=[ (  (time,length-100),refpos,('sin',amp,puls,angle)   ) ,
                    (time+length,refpos ) ]


    def animate(self):
        #print 'yay', self.current_anim
        if not self.steps:
            self.rm_state('anim')
            try:
                self.rem_from_group(self.parent.animated)
            except:
                pass
            return False
        todo=[]
        time=pg.time.get_ticks()
        for  t in tuple(self.steps) :
            if t=='hide' or t[1]=='hide' and time> t[0]:
                todo.append( (0.,0.,0.,0.) )
            elif isinstance(t,basestring):
                todo.append(t)
            elif len(t)>1:
                #Time and event
                try:
                    t1,t2=t[0][0],t[0][0]+ t[0][1] #Duration
                    if t1<=time<t2:
                        if len(t[1])==4: #Color
                            todo.append( [i+float(j-i)*(time-t1)/t[0][1] for i,j in zip(*t[1:3])] )
                        elif  len(t[1])==2: #Movement
                            ref=array(t[1])
                            if str(t[2][0])!=t[2][0]: #coordinates
                                td=[]
                                for i,j in zip(*t[2:4]):
                                    frac=i+float(j-i)*(time-t1)/t[0][1]
                                    if isinstance(i,float):
                                        frac*=self.rect.size[len(td)]
                                    td.append(int(frac))

                            else: #Movement with function

                                if t[2][0]=='sin':

                                    amp,puls,angle=t[2][1:]
                                    if isinstance(amp,float):
                                        amp*=self.rect.h#sum(self.rect.size*array(sin(angle),cos(angle) ))

                                    val= amp*sin(puls*time-t1)
                                    td=array((int(val*sin(angle)),int(val*cos(angle))))

                            todo.append( ref+ td )
                        else:
                            print 'Unknown type of animation', t[1]
                    elif t2<time:
                        self.steps.remove(t)
                except:
                    #Punctual
                    if t[0]<=time:
                        todo.append(t[1])
                        self.steps.remove(t)
                        break
            else:
                todo.append(t)
                self.steps.remove(t)
                break

        if hasattr(self,'alpha'):
            albase=self.alpha/255.
        else:
            albase=1.
        anim_mod=array((1.,1.,1.,albase))
        for t in todo:
            if self.special_anim(t):
                continue
            try:
                if len(t)==4:
                    # Color
                    anim_mod*=array(t,dtype=float)
                elif len(t)==2:
                    #Movement
                    #print time,self,self.current_anim
                    self.rect.center=array(t)
            except:
                pass
        self.anim_mod=anim_mod
        self.set_state('anim',True)
