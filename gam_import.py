# -*- coding: utf-8 -*-

import sys,site

#site.addsitedir("/home/neve/Documents/Projets/")
from graphview import *


class GameVariable(DataItem):
    vid=0
    dft={'name':'Variable',
        'val':0.,
        }

    def __init__(self,**kwargs):
        self.type='variable'
        self.vid=GameVariable.vid
        self.name='Variable{}'.format(self.vid)
        DataItem.__init__(self,**kwargs)
        GameVariable.vid+=1
    def __repr__(self):
        return '{}: {}'.format(self.name,self.val)

class EditorSM(BasicSM):
    def __init__(self,*args,**kwarsg):
        BasicSM.__init__(self,*args,**kwarsg)
        user.music.stop()

    def receive_signal(self,signal,*args,**kwargs):
        sgn=signal.type
        if 'set_' in sgn:
            return self.play('load')
