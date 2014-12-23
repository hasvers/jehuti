from gv_winfieldcont import *


class Window(FieldContainer):
    per_pixel_alpha=0
    pause=0
    clickthrough=False #is the window opaque to mouse events?
    exit_method=lambda e=None:e

    def __init__(self,interface,(w,h),*args,**kwargs):
        self.interface=interface
        margin=kwargs.pop('margin',graphic_chart['window_margin'])
        w,h=max((w,3*margin)),max((h,3*margin))
        FieldContainer.__init__(self,interface,size=(w,h),margin=margin,**kwargs)
        self.alpha=graphic_chart['window_base_alpha']
        self.field_commands={ 'always':['confirm'],
            'confirm':[(self.unselect,( ) ) ],
            'queue':['do'],
            'emptyqueue':['do'] }
        self.queue=[]
        self.skin_name='windowskin'
        for i,j in kwargs.iteritems():
            if i =='alpha':
                self.alpha=j
            if i=='fixsize':
                self.fixsize=j
            if i=='exit_method' :
                self.exit_method=j
            if i=='oneshot' and j:
                self.field_commands['confirm']+=['exit']
                self.field_commands['cancel']=['exit']
            if i =='ephemeral' and j:
                self.set_command('unhover','exit')
            if i=='skin':
                self.skin_name=j
            if i=='clickthrough':
                self.clickthrough=j
        self.index=0
        self.paint()
        if self.pause:
            user.pause()

    def set_state(self,state,*args,**kwargs):
        if state!='idle':
            self.exe_command(state)
        return FieldContainer.set_state(self,state,*args,**kwargs)

    def rm_state(self,state,*args,**kwargs):
        self.exe_command('un'+state)
        return FieldContainer.rm_state(self,state,*args,**kwargs)

    def ask_confirm(self,val=True):
        if val :
            if  'confirm' in self.field_commands['always']:
                self.field_commands['always'].remove('confirm')
        else :
            if not 'confirm' in self.field_commands['always']:
                self.field_commands['always'].append('confirm')

    def set_command(self,source,method,**kwargs):
        com=self.field_commands
        #print self, 'setcommand',source,method
        if not isinstance(method,basestring) and not hasattr(method,'__iter__'):
            method=(method, () )
        if not isinstance(method,list):
            method = [method]
        if source in com :
            replace = False
            for c in range(len(com[source])):
                if com[source][c][0]==method[0][0]: #if same output method, replace command
                   com[source][c]=method[0]
                   replace = True
            if not replace :
                com[source]+=method
        else :
            com[source]=method[:]
        if kwargs.get('queue',False):
            self.queue.append(source)
        if self.queue:
            self.exe_command('queue')

    def rem_command(self,source,method=None,**kwargs):
        com=self.field_commands
        if method and not isinstance(method,list):
            method = [method]
        if source in com :
            if kwargs.get('delete',False):
                del com[source]
            elif not method :
                com[source]=[]
            else :
                for m in tuple(com[source]):
                    if m in method or m[0] in method :
                        com[source].remove(m)
            if not com.get(source) and source in self.queue:
                self.queue.remove(source)
            if not self.queue :
                self.exe_command('emptyqueue')

    def rem_from_queue(self,source):
        if source in self.queue:
            self.queue.remove(source)
            if not self.queue :
                self.exe_command('emptyqueue')

    def exe_command(self,source,**kwargs):
        com=self.field_commands
        method = kwargs.pop('command',False)
        #print 'execommand',self,source, source in com
        if not source in com :
            if not method:
                return False
            com[source]=[]
        queue=[]
        if  method:
            self.set_command(source,method,kwargs)
        else :
            newval=kwargs.pop('val',None)
            if newval :
                for i in range(len(com[source])):
                    if isinstance(com[source][i],tuple) and newval:
                        if isinstance(newval,list):
                            #accept only the proper number of arguments
                            com[source][i]=(com[source][i][0],newval.pop(0))
                        else :
                            com[source][i]=(com[source][i][0],newval)
                            newval=None
        exe = False
        if 'do' in com[source] :
            #sources with 'do' act alone (vs 'confirm')
            if 'do' in com :
                queue+=['do']
            exe=True
            allcom=com[source]
        else :
            queue=self.queue
            self.exe_command('queue')
            allcom=com[source]+com['always']

        if not source in queue :
            queue+=[source]

        if 'cancel' in allcom :
            self.queue=queue=[]
            if 'cancel' in com :
                queue+=['cancel']
            exe=True
        if 'confirm' in allcom :

            """for c in com.keys() :
                if not isinstance(c,basestring):
                    met=com.pop(c,None)
                    if met :
                        queue+=met"""

            if 'confirm' in com and not 'confirm' in self.queue:
                self.queue+=['confirm']
            exe=True

        if exe:
            while queue :
                s=queue.pop(0)
                comms=com[s][:]
                if 'exit' in comms:
                    comms.remove('exit')
                    for z in com.get('exit',()):
                        comms.append(z)
                    comms.append('exit')
                for i in comms:
                    if isinstance(i,basestring) :
                        if i =='exit' :
                            if i in com : #exit methods
                                [j[0](*j[1]) for j in com[i] if j[0]]

                            self.queue=[]
                            queue=[]
                            for src in tuple(self.field_commands.keys()) :
                                if not isinstance(src,basestring) :
                                    del self.field_commands[src]
                            return self.exit_method()
                    else :
                        if i[0]:
                            i[0](*i[1])

    def add(self,field,**kwargs):
        for i,j in kwargs.iteritems():
            if i=='output_method':
                if j=='confirm' :
                    self.ask_confirm()

        field = FieldContainer.add(self,field,**kwargs)
        self.paint()
        return field

    def drop_menu(self,anchor,struct,**kwargs):
        if not hasattr(struct,'__iter__'):
            struct=struct()
        self.parent.float_menu(struct,ephemeral=False)
        print anchor
        self.parent.window['floatmenu'].rect.topleft = anchor.rect.midbottom
        self.parent.window['floatmenu'].draggable=False

    def resize(self,(w,h),*args,**kwargs):
        oldsize=self.size
        FieldContainer.resize(self,(w,h),*args,**kwargs)
        if oldsize!=(w,h):
            self.paint()

    def skin(self,size=None):#,offset=None):
        name=self.skin_name

        #self.image.fill(COLORKEY)
        if not name :
            #if size is None:
                #size = self.image.get_rect().size
            #self.bg=pg.surface.Surface(size)
            #self.bg.fill(COLORKEY)
            #self.image.set_colorkey(COLORKEY)
##            self.image.set_alpha(self.alpha,pg.RLEACCEL)
            #self.image.blit(self.bg,offset)
            return False
        wskin=graphic_chart[name]
        rect=wskin.get_rect()
        bg=pg.surface.Surface((rect.h,rect.h),0,wskin)
        bg.blit(wskin,(0,0))
        box=pg.surface.Surface((rect.w-rect.h,rect.w-rect.h),0,wskin)
        box.blit(wskin,(-rect.h,0))
        tilew, tileh = int(box.get_width()/3), int(box.get_height()/3)
        x,y= (0,0)
        if size is None:
            size=self.rect.size
        xx, yy = size
        w,h=self.rect.w,self.rect.h
        src = pg.rect.Rect(0, 0, tilew, tileh)
        dest = pg.rect.Rect(0, 0, tilew, tileh)

        surf=pg.surface.Surface(size,0,self)

        surf.blit(pg.transform.smoothscale(bg,size),(0,0))
        # Render the top side of the box
        surf.set_clip(pg.Rect(x+tilew,y,w-tilew*2,tileh))
        src.x,src.y,dest.y = tilew,0,y
        for dest.x in range(x+tilew, xx-tilew*2+tilew, tilew):
            surf.blit(box,dest,src)

        # Render the bottom side
        surf.set_clip(pg.Rect(x+tilew,yy-tileh,w-tilew*2,tileh))
        src.x,src.y,dest.y = tilew,tileh*2,yy-tileh
        for dest.x in range(x+tilew,xx-tilew*2+tilew,tilew):
            surf.blit(box,dest,src)

        # Render the left side
        surf.set_clip(pg.Rect(x,y+tileh,xx,h-tileh*2))
        src.y,src.x,dest.x = tileh,0,x
        for dest.y in range(y+tileh,yy-tileh*2+tileh,tileh):
            surf.blit(box,dest,src)

        # Render the right side
        surf.set_clip(pg.Rect(xx-tilew,y+tileh,xx,h-tileh*2))
        src.y,src.x,dest.x=tileh,tilew*2,xx-tilew
        for dest.y in range(y+tileh,yy-tileh*2+tileh,tileh):
            surf.blit(box,dest,src)

        # Render the upper-left corner
        surf.set_clip()
        src.x,src.y,dest.x,dest.y = 0,0,x,y
        surf.blit(box,dest,src)

        # Render the upper-right corner
        src.x,src.y,dest.x,dest.y = tilew*2,0,xx-tilew,y
        surf.blit(box,dest,src)

        # Render the lower-left corner
        src.x,src.y,dest.x,dest.y = 0,tileh*2,x,yy-tileh
        surf.blit(box,dest,src)

        # Render the lower-right corner
        src.x,src.y,dest.x,dest.y = tilew*2,tileh*2,xx-tilew,yy-tileh
        surf.blit(box,dest,src)

        #self.bg=surf
        #self.image.blit(self.bg,offset)
        #self.image.set_colorkey(COLORKEY)
#        self.image.set_alpha(self.alpha,pg.RLEACCEL)
        return surf

    def paint(self):
        bg=self.skin()
        if bg:
            self.bg=pg.surface.Surface(self.rect.size)
            self.bg.fill(COLORKEY)
            self.bg.blit(bg,(0,0))
            self.bg.set_colorkey(COLORKEY)
            self.image.set_colorkey(COLORKEY)
            self.image.blit(self.bg,(0,0))
        else:
            print 'ERROR: Window has no background!',self
        try:
            self.dirty=1
            self.draw() #draw is the fieldcontainer method
        except:
            pass

    def color_mod(self,state):
        if state == 'anim':
            return self.anim_mod
        if state == 'hover':
            dft=graphic_chart['window_hover_alpha']
            if self.alpha<dft:
                return (1,1,1,float(dft)/self.alpha)
        mod =graphic_chart.get('window_'+state+'_color_mod',(1,1,1,1))
        if self.alpha:
            mod=mod[:3]+(1,)
        return mod

    def update(self):
        self.catch_new()
        self.group.update()
        self.draw()
        if UI_Widget.update(self):
            self.dirty=1

    def event(self,event,**kwargs):
        if FieldContainer.event(self,event,**kwargs):#,refpos=array(self.abspos())+array(self.active_rect.topleft),**kwargs) :
            return True
            #if self.container.event(event):
            #    return True
        return self.window_event(event)

    def window_event(self,event):
        return False

    def kill(self,recursive=True):
        FieldContainer.kill(self,recursive)
        if self.pause:
            user.pause(False)

class DragWindow(Window):
    draggable=True

    def __init__(self,dragarea,*args,**kwargs):
        Window.__init__(self,*args,**kwargs)
        for i, j in kwargs.iteritems():
            if 'drag' in i:
                self.draggable = j
        self.dragarea=dragarea

    def event(self,event,**kwargs):
        if self.is_grabbed :
            return self.window_event(event,**kwargs)
        else :
            return Window.event(self,event,**kwargs)


    def window_event(self,event,**kwargs):
        if not self.draggable :
            return False
        if event.type == pg.MOUSEBUTTONDOWN and event.button ==1 and not self.hovering:
            user.focus_on(self)
            return True
        if user.focused_on==self and event.type==pg.MOUSEMOTION:
            user.unfocus()
            user.grab(self)
            #print self.is_grabbed, evts
        if self.is_grabbed :

            if event.type == pg.MOUSEBUTTONUP:
                user.ungrab()
            if event.type==pg.MOUSEMOTION:
                rect = self.rect.move(event.rel)
                bound=self.dragarea.get_rect()
                if bound.contains(rect):
                    self.rect.move_ip(event.rel)
                    if self.parent :
                        pos =self.parent.pos[self]
                        pos=array(pos)+array(event.rel)
                        self.parent.pos[self]=tuple(pos)
                    return True
        return False

class FloatMenu(DragWindow):

    def __init__(self,*args,**kwargs):
        struct=kwargs.pop('struct',None)
        DragWindow.__init__(self,*args,**kwargs)
        if struct != None:
            self.parse(struct)

class InputMenu(FloatMenu):

    def parse(self,struct):
        for i in range(len(struct)):
            line = struct[i]
            self.add('text',val=line[0],pos=(i,0))
            self.add('input',val=line[2],output_method=line[1],pos=(i,1))

class DecoratedWindow(Window):
    decor_mrg=array([0,0,0,0])

    def __init__(self,interface,(w,h),*args,**kwargs):
        mrg=self.decor_mrg
        Window.__init__(self,interface,(w+mrg[0]+mrg[2],h+mrg[1]+mrg[3]),*args,**kwargs)

    def mrg(self,sizeonly=True):
        mrg=Window.mrg(self,sizeonly)
        if not sizeonly:
            return mrg +self.decor_mrg
        else :
            decmrg=self.decor_mrg.copy()
            decmrg[2:]+=decmrg[:2]
            decmrg[:2]=0
            return mrg +decmrg


    def paint(self):
        size=self.rect.size-(self.decor_mrg[:2]+self.decor_mrg[2:])
        offset=self.decor_mrg[:2]
        bg=Window.skin(self,size)
        self.bg=pg.surface.Surface(self.rect.size,0,self)
        self.bg.fill(COLORKEY)
        self.bg.blit(bg,offset)
        self.image.blit(self.bg,(0,0))
        self.image.set_colorkey(COLORKEY)
        self.dirty=1
        self.draw()

class SpeechBalloon(DecoratedWindow):

    freepos=False #TODO: compute best position for window and point size having only absolute position of point and size of window
    corner_radius=20


    def __init__(self,interface,size,*args,**kwargs):
        (w,h)=size
        self.point=kwargs.pop('point',(0,0,0,0))
        self.make_decor_mrg(size)
        kwargs.setdefault('alpha',200)
        kwargs.setdefault('maxsize',array(interface.rect.size)*.5)

        DecoratedWindow.__init__(self,interface,(w,h),*args,**kwargs)
        user.focus_on(self)

    def make_decor_mrg(self,size=None):
        px,py,ppx,ppy=self.point
        if size is None :
            size=self.rect.size-(self.decor_mrg[:2]+self.decor_mrg[2:])
        w,h=size
        mrg=[0,0,0,0]
        if px<0:
            mrg[0]=-px
        if ppx>0:
            mrg[2]=ppx
        if py<0:
            mrg[1]=-py
        if ppy>0:
            mrg[3]=ppy
        self.decor_mrg=array(mrg)

    def set_point(self,point):
        size=self.rect.size-(self.decor_mrg[:2]+self.decor_mrg[2:])
        self.point=point
        self.make_decor_mrg(size)
        self.resize(size+(self.decor_mrg[:2]+self.decor_mrg[2:]))

    def paint(self):
        self.make_decor_mrg()
        size=self.rect.size-(self.decor_mrg[:2]+self.decor_mrg[2:])
        offset=self.decor_mrg[:2]
        bg=Window.skin(self,size)
        self.bg=pg.surface.Surface(self.rect.size,0,self)
        self.bg.fill(COLORKEY)
        self.bg.set_colorkey(COLORKEY)

        if array(self.point).any():
            pt=self.point
            point=array([0,0])
            if pt[0]:
                point[0]=pt[0]
            else:
                point[0]=self.rect.right
            if pt[1]:
                point[1]=pt[1]
            else:
                point[1]=self.rect.bottom
            wskin=graphic_chart[self.skin_name]
            rect=wskin.get_rect()
            color=wskin.get_at((rect.h+2,2))
            #color=(255,255,255,255)
            center=self.rect.center
            _r=self.corner_radius
            perp1 = (center[0]-_r/2, center[1]+_r/2)
            perp2 = (center[0]+_r/2, center[1]-_r/2)

            pts = (point, perp1, perp2)
            pg.draw.polygon(self.bg, color, pts, 0)
        self.bg.blit(bg,offset)
        self.bg.set_colorkey(COLORKEY)
        #self.image.blit(self.bg,(0,0))
        self.dirty=1
        self.draw()


    def event(self,evt,*args,**kwargs):
        if (evt.type== pg.MOUSEBUTTONDOWN and evt.button==1 and self.is_hovering) or (
                evt.type==pg.KEYDOWN and evt.key in (pg.K_SPACE,pg.K_RETURN)):
            self.closing_event()
            return True
        return False
        #try:
            #if evt.button==1:
                #self.interface.close(self)
                #return True
        #except:
            #pass
        #if DecoratedWindow.event(self,evt,*args,**kwargs):
                #self.interface.close(self)
                #return True
        #return False

    def closing_event(self):
        self.set_command('queue','exit')
        self.exe_command('queue')
        self.set_anim('disappear',len=ANIM_LEN['short'],affects=[self])

    def react(self,evt):
        if evt.type=='anim_stop' and evt.args[0].anim=='disappear':
            self.interface.close_balloon(self)
            #profiler.disable()
            #prolog('eventlog.dat')
            #print 'profilend', pg.time.get_ticks()
        #if evt.type=='anim_start' and evt.args[0].anim=='appear':
            #print 'profilstart', pg.time.get_ticks()
            #profiler.enable()
