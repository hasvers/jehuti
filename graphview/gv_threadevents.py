# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

from gv_events import *

#Could include animations, as events that affect nothing (thus no passing around)

class ThreadEvent(Event):
    #Event occuring over time
    #States: 1 - busy; 2- done (possible to jump from 0 to 2 or 2 to 0)
    #Two modes when going from 1 to 1 (i.e. still busy doing the event):
        # absolute, i.e. finite duration with absolute starting point &
        # step-by-step i.e.  finite number of mid-points (e.g. anim frames)

    repeatable=1
    def __init__(self,*args,**kwargs):
        self.block_thread=kwargs.get('block_thread',0) #for sequential events
        self.tinit=kwargs.get('tinit',None)
        self.mode=kwargs.pop('mode','step')
        if self.mode=='step':
            self.step=0
        self.duration=kwargs.pop('duration',1)

        Event.__init__(self,*args,**kwargs)
        self.add_state(2,pred=1)
        self.states.add_edge(1,1)
        self.states.add_edge(0,2)
        self.states.add_edge(2,0)


    def prepare(self,edge,handler=None,*args,**kwargs):
        if edge ==(0,1) :
            if self.tinit is None:
                if self.mode=='abs':
                    self.tinit=kwargs.get('tinit',pg.time.get_ticks() )
                else:
                    self.tinit=kwargs.get('time',0)
            return self.prep_init(handler)
        if edge==(1,1):
            if self.mode=='abs':
                pass
            elif self.mode =='step':
                pass
            return 1
        if edge ==(1,0) :
            return self.prep_uninit(handler)
        if edge ==(1,2) :
            return self.prep_end(handler)
        if edge ==(2,1) :
            return self.prep_unend(handler)
        if edge ==(2,0) :
            return self.prep_undo(handler)

    def prep_init(self,*args,**kwargs):
        return True
    def prep_uninit(self,*args,**kwargs):
        self.step=0
    def prep_end(self,*args,**kwargs):
        return True
    def prep_unend(self,*args,**kwargs):
        return True
    def prep_undo(self,*args,**kwargs):
        self.step=0

    def run(self,state,*args,**kwargs):
        if state==0:
            return self.undo(*args,**kwargs)
        if state==1:
            if self.mode=='abs':
                fraction= kwargs.get('time',pg.time.get_ticks()-self.tinit)/float(self.duration)
            elif self.mode =='step':
                if 'time' in kwargs:
                    self.step=kwargs['time']-self.tinit
                else:
                    self.step+=1
                fraction= (self.step)/float(self.duration)
            if fraction >1:
                return False
            return self.do(fraction,*args,**kwargs)
        if state==2:
            return self.end(*args,**kwargs)

    def do(self,fraction,*args,**kwargs):
        pass
    def undo(self,*args,**kwargs):
        pass
    def end(self,*args,**kwargs):
        pass

class ThreadMoveEvt(ThreadEvent):
    desc='Move'
    def __init__(self,item,graph,pos,**kwargs):
        super(ThreadMoveEvt, self).__init__(type='move',**kwargs)
        self.item = item
        self.pos=pos
        self.graph=graph


    def __repr__(self):
        return '{} {} {}'.format(self.desc,self.item,self.pos)

    def affects(self):
        return (self.item, self.graph)+tuple(self._affects)

    def prep_init(self,*args,**kwargs):
        self.oldpos=self.graph.pos[self.item]

    def do(self,fraction,*args,**kwargs):
        if fraction and not tuple(self.pos)==tuple(self.oldpos):
            dpos = tuple(int(i*fraction) for i in array(self.pos)-self.oldpos)
            self.graph.pos[self.item]=self.oldpos+array(dpos)
            return True
        return False

    def end(self ,*args,**kwargs):
        if tuple(self.graph.pos[self.item])!=tuple(self.pos):
            self.graph.pos[self.item]=self.pos
            return True
    def undo(self,*args,**kwargs):
        if tuple(self.graph.pos[self.item])!=tuple(self.oldpos):
            self.graph.pos[self.item]=self.oldpos
            return True

class FadeEvt(ThreadEvent):
    desc='Fade'
    def __init__(self,mod1,mod2,**kwargs):
        super(FadeEvt, self).__init__(type='fade',**kwargs)
        self.mod=(mod1,mod2)
        self.surface=kwargs.get('surface',None)
        #to xfade to/from an image instead (e.g. splash screen)

    def __repr__(self):
        return 'Fade {} -> {}'.format(self.mod[0],self.mod[1])


    def prep_init(self,handle,*args,**kwargs):
        ui=handle.parent
        if self.surface:
            ui.veils['fade']=self.surface
            return 1
        if ui.screen.get_flags()&pg.SRCALPHA:
            ui.veils['fade']=pg.surface.Surface(ui.screen.get_rect().size,pg.SRCALPHA)
        else:
            ui.veils['fade']=pg.surface.Surface(ui.screen.get_rect().size)
        color=tuple(max(0,min(255,i)) for i in self.mod[0])
        ui.veils['fade'].fill(color)
        ui.veils['fade'].set_alpha(color[3] )

    def do(self,fraction,handle,*args,**kwargs):
        ui=handle.parent
        if 0<fraction<1:
            color=tuple(max(0,min(255,rint(x))) for x in (
                self.mod[0]+fraction*(array(self.mod[1])-self.mod[0]) ) )
            try:
                if not self.surface:
                    ui.veils['fade'].fill( color)
                ui.veils['fade'].set_alpha(color[3])
                return True
            except Exception as e:
                print e
                pass
        return False

    def end(self ,handle,*args,**kwargs):
        ui=handle.parent
        if self.mod[1][3]==0:
            try:
                del ui.veils['fade']
            except:
                pass
        return True

    def undo(self,handle,*args,**kwargs):
        ui=handle.parent
        if self.mod[0][3]==0:
            try:
                del ui.veils['fade']
            except:
                pass
            return True
        return False

class PanEvt(ThreadEvent):
    desc='Pan'
    def __init__(self,scene,rel,**kwargs):
        super(PanEvt, self).__init__(type='pan',**kwargs)
        self.rel=rel
        self.scene=scene

    def __repr__(self):
        return '{} {} {}'.format(self.desc,self.scene,self.rel)

    def affects(self):
        return (self.scene,)+tuple(self._affects)

    def prep_init(self,*args,**kwargs):
        self.oldpos={l:self.scene.get_info(l,'offset') for l in self.scene.layers}

    def do(self,fraction,*args,**kwargs):
        if 0<fraction<1:
            rel=fraction*array(self.rel)
            scene=self.scene
            for l in scene.layers:
                offset=tuple(int(i*(1.-scene.get_info(l,'distance'))) for i in rel)
                scene.set_info(l,'offset',self.oldpos[l]+array(offset))
            return True
        return False

    def end(self ,*args,**kwargs):
        scene=self.scene
        for l in scene.layers:
            offset=tuple(int(i*(1.-scene.get_info(l,'distance'))) for i in self.rel)
            offset+=array(self.oldpos[l])
            scene.set_info(l,'offset',offset,additive=False)
        return True

    def undo(self,*args,**kwargs):
        scene=self.scene
        for l in scene.layers:
            scene.set_info(l,'offset',self.oldpos[l],additive=False)
        return True




class ZoomEvt(ThreadEvent):
    desc='Zoom'
    def __init__(self,scene,target,**kwargs):
        super(ZoomEvt, self).__init__(type='zoom',**kwargs)
        self.target=target
        self.scene=scene

    def __repr__(self):
        return '{} {} {}'.format(self.desc,self.scene,self.target)

    def affects(self):
        return (self.scene,)+tuple(self._affects)

    def prep_init(self,*args,**kwargs):
        self.oldzoom={l:self.scene.get_info(l,'zoom') for l in self.scene.layers}
        self.oldpos={l:self.scene.get_info(l,'offset') for l in self.scene.layers}


    def do(self,fraction,*args,**kwargs):
        if 0<fraction<1:
            handler=args[0]
            target= fraction*(self.target-1)
            scene=self.scene
            for l in scene.layers:
                zoom=1+target*(1.-self.scene.get_info(l,'distance'))
                scene.set_info(l,'zoom',self.oldzoom[l]*zoom)
                offset=(zoom-1)*array(handler.parent.screen.get_rect().size)/2
                scene.set_info(l,'offset',array(self.oldpos[l]-offset,dtype='int'))
            return True
        return False

    def end(self ,*args,**kwargs):
        scene=self.scene
        handler=args[0]
        for l in scene.layers:
            zoom=1+(self.target-1)*(1.-self.scene.get_info(l,'distance'))
            scene.set_info(l,'zoom',self.oldzoom[l]*zoom)
            offset=(zoom-1)*array(handler.parent.screen.get_rect().size)/2
            scene.set_info(l,'offset',array(self.oldpos[l]-offset,dtype='int'))
        return True

    def undo(self,*args,**kwargs):
        scene=self.scene
        handler=args[0]
        for l in scene.layers:
            scene.set_info(l,'zoom',self.oldzoom[l])
            scene.set_info(l,'offset',array(self.oldpos[l],dtype='int'))
        return True
