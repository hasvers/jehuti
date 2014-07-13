# -*- coding: utf-8 -*-
from gv_uibasics import *

class Animation(object):
    perpetual=False

    def __init__(self,*args,**kwargs):
        self.steps=[]
        self.start=0
        self.end=-1
        self.set_anim(*args,**kwargs)

    @property
    def has_ended(self):
        return ( self.end>0 and  pg.time.get_ticks()>self.end )

    @property
    def has_started(self):
        return ( self.start>0 and  pg.time.get_ticks()>self.start )

    def set_anim(self,anim,**kwargs):
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

