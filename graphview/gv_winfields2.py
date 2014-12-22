# -*- coding: utf-8 -*-
from gv_winfields import *

class InputField(TextField):
    focus_mark='|'
    allchars = 'all'
    charlist =('_','-','.')
    fixsize=True
    scrollable=True
    loop=False #Is it possible to go from beginning to end?
    interpret=False
    def __init__(self,parent,**kwargs):
        kwargs.pop('draw',None)
        TextField.__init__(self,parent,draw=False,**kwargs)
        self.val=str(self.val)
        self.focusable=True
        self.charlimit=None
        for i, j in kwargs.iteritems() :
            if i in ('charlimit','maxlen') :
                self.charlimit = j
            if i =='allchars':
                self.allchars=j
            if i =='charlist':
                self.charlist=j
            if i=='loop':
                self.loop=j
        self.moveindex(0)
        self.last_change_timestamp=pg.time.get_ticks()

    def set_val(self,val):
        self.val=str(val)
        if self.index>len(self.val)+1:
            self.index =-1
        self.moveindex(0)

    def output(self,*args):
        self.last_change_timestamp=pg.time.get_ticks()
        return TextField.output(self,*args)

    def moveindex(self,step,redraw=True):
        if step == 'd' or step == 'u' :
            if self.maxlines==1 or len(self.lines) <2:
                return False
            line = 0
            lb = [sum(self.linelen[:i]) for i in xrange(1,len(self.lines))]
            while line < len(lb) and self.index > lb[line]:
                line +=1
            if line != 0 :
                local_index=self.index-lb[line-1]
            else :
                local_index = self.index
            if step == 'd' :
                if line==len(lb):
                    if self.loop:
                        line=0
                else:
                    line+=1
            elif line!=0 or self.loop:
                line-=1
            if line ==0:
                lbase=0
            else:
                lbase=lb[line-1]
            self.index=min(len(self.val),lbase+min(local_index,self.linelen[line]))
        else :
            l=len(self.val)+1
            if l>1 and (self.loop or not step ):
                self.index = (self.index + step + l) % l
            else :
                self.index=max(0,min(self.index+step,l-1))
        if redraw :
            if  hasattr(self,'lines') and self.lines:
                l,i=0,0
                xoff,yoff=0,0
                while l+self.linelen[i]<self.index and i<len(self.lines)-1:
                    i+=1
                    l+=self.linelen[i]
                    yoff+=self.linehei[i]
                if len(self.lines)>1:
                    yoff+=self.linehei[i]
                line = self.lines[i][:]
                srec=array(self.rect.size) -self.padding[:2]-self.padding[2:]
                if line:
                    l= self.index- l
                    c=line.pop(0)
                    xoff=c.rect.left
                    while l>0 and line:
                        l-= len(c.txt)
                        c=line.pop(0)
                    xoff=c.rect.right-xoff
                    xoff,yoff = (srec - self.offset)-array([xoff,yoff])
                    self.offset+=xoff,yoff
                    self.offset[self.offset>0]=0
            self.redraw()

    def rm_state(self,*args,**kwargs):
        TextField.rm_state(self,*args,**kwargs)
        if args[0]=='focus':
            self.moveindex(0)

    def event(self,event,*args,**kwargs):
        #if event.type == pg.MOUSEMOTION :  #Why the hell did I put this?
            #return True
        if event.type == pg.MOUSEBUTTONDOWN:
            if False and self.is_focused:
                user.unfocus()
            elif event.button==1 :
                user.focus_on(self)
                self.index=self.locate(self.parent.mousepos(self))
                self.moveindex(0)
            return True
        if self.is_focused and event.type == pg.KEYDOWN :
            val=self.val
            if event.key == pg.K_LEFT :
                self.moveindex(-1)
            elif event.key == pg.K_RIGHT :
                self.moveindex(1)
            elif event.key == pg.K_DOWN :
                self.moveindex('d')
            elif event.key==pg.K_UP :
                self.moveindex('u')
            elif event.key == pg.K_BACKSPACE:
                if len(self.val)>1  and self.index!=0 :
                    self.moveindex(-1,False)
                    if self.index == -1 :
                        self.val = self.val[:-1]
                    else :
                        self.val = ''.join( list(self.val)[:self.index] + list(self.val)[self.index+1:] )
                else :
                    if len(self.val)<=1:
                        self.val=''
                self.moveindex(0)
            elif event.key ==pg.K_RETURN :
                if len(self.lines)>=self.maxlines:
                    return False
                l =list(self.val)
                l.insert(self.index, '\n')
                self.val= ''.join(l)
                self.moveindex(1)
            elif array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
                if event.key==pg.K_v:
                    test=str(clipboard.paste())
                    if test:
                        l =list(self.val)
                        l.insert(self.index, test)
                        self.val= ''.join(l)
                        self.moveindex(len(test))
                if event.key==pg.K_c:
                    clipboard.copy(self.val)
            elif event.key == pg.K_TAB:
                try:
                    return self.parent.next_field()
                except:
                    return False
            else :
                euni= event.unicode
                if (self.allchars=='all' or
                        (self.allchars=='alnum' and euni.isalnum()) or
                        (self.allchars=='alpha' and euni.isalpha()) or
                        (self.allchars=='num' and euni.isdigit()) or
                        (self.allchars=='relnum' and euni.isdigit() or (euni=='-' and self.index==0) )
                        or event.unicode in self.charlist) and (
                            not self.charlimit or len(self.val)<self.charlimit):
                    if euni:
                        l =list(self.val)
                        l.insert(self.index, euni)
                        self.val= ''.join(l)
                        self.moveindex(1)

                else :
                    return False
            #self.redraw()
            if self.val != val :
                if self.allchars=='relnum' and self.val=='-':
                    self.set_val('-0')
                self.output()
            return True
        return False

class ExtSelField(TextField):
    #Textfield whose value comes from external events (typically selection from canvas)
    selectable=True
    def __init__(self,parent,**kwargs):
        self.selsource=kwargs.pop('selsource')
        self.seltype=kwargs.pop('seltype',None)
        self.evttype=kwargs.pop('evttype','select')
        TextField.__init__(self,parent,**kwargs)
        parent=self.parent
        while not hasattr(parent,'interface'):
            parent=parent.parent
        parent.interface.depend.add_dep(self,self.selsource)

    def react(self,evt):
        if self.is_selected and self.evttype in evt.type :
            if self.seltype=='event':
                #outputs the EVENT rather than the ITEM
                self.parent.unselect(self)
                self.set_val(evt)
                self.output()
                user.evt.undo(evt,1,ephemeral=True)
                user.evt.data.rem_event(evt)
                #print user.evt.stack
                return True
            elif (self.seltype is None or self.seltype==item.type):
                try:
                    item=evt.args[0]
                except:
                    try:
                        item=evt.item
                    except:
                        return False
                try:
                    item =item.item
                except:
                    pass
                self.parent.unselect(self)
                self.set_val(item)
                self.output()
                #if not hasattr(evt,'item'):
                    #evt=SelectEvt(evt.args[0], source=evt.source,affects=(evt.args[0],) )
                    #evt.state=0
                    #user.evt.pass_event(evt,self,1)
                #else:
                if  hasattr(evt,'item'): #this is a SelectEvt, not a simple signal
                    user.evt.go(evt,0)
                return True
        return False

    def event(self,event,*args,**kwargs):
        if event.type == pg.MOUSEBUTTONDOWN and event.button==1 :
            self.parent.select(self)
            if not self.is_selected:
                #Inverted from normal textfield: output activated if field NOT selected
                return self.output()
            else :
                return self.stop_output()
        else:
            TextField.event(self,event,*args,**kwargs)

    def kill(self,*args):
        parent=self.parent
        if self.is_selected:
            parent.unselect(self)
        while not hasattr(parent,'interface'):
            parent=parent.parent
        parent.interface.depend.rem_dep(self,self.selsource)
        TextField.kill(self,*args)


class MultiTextField(TextField):
    fixsize=False
    val=None
    values=()

    def __init__(self,parent,values,**kwargs):
        WindowField.__init__(self,parent)
        self._maxsize=[False,False]
        w,h=None,None
        for i,j in kwargs.iteritems():
            if i in ('w','wid','width') :
                self.width=j
                self._maxsize[0]=j
            if i in ('h','hei','height') :
                self.height=j
                self._maxsize[1]=j
        if 'val' in kwargs and not kwargs['val'] in values:
            kwargs['val']=self.val
        #nkwargs.pop('val')
        self.set_values(values,0)
        super(MultiTextField, self).__init__(parent,w=self.width,h=self.height,**kwargs)


    def set_values(self,values,redraw=1):
        if values==self.values:
            return False
        wtemp=0
        htemp=0
        #img = pg.surface.Surface(graphic_chart['screen_size'],pg.SRCALPHA)
        for v in values:
            txt=str(v)
            img,size=self.write(txt,return_bb=True)
            if size[0]>wtemp:
                wtemp=size[0]
            if size[1]>htemp:
                htemp=size[1]
        if not self._minsize:
            self._minsize=wtemp,htemp
        if not self.fixsize:
            if not self.maxsize[0]:
                self.width=wtemp
            if not self.maxsize[1]:
                self.height=htemp
        self.values=values
        if not self.val in values:
            self.val=values[0]
        if redraw:
            self.redraw()

    def next_val(self):
        idx=self.values.index(self.val)+1
        if self.set_val( self.values[ idx%len(self.values)]):
            self.output()
            return True
        return False

    def prev_val(self):
        idx=self.values.index(self.val)-1+len(self.values)
        if self.set_val( self.values[ idx%len(self.values)]):
            self.output()
            return True
        return False

    def set_val(self,val,*args,**kwargs):
        if val in self.values:
            return super(MultiTextField,self).set_val(val,*args,**kwargs)
        WindowField.set_val(self,val)
        try:
            val=self.values[val]
            return self.set_val(val,*args,**kwargs)
        except :
            return False

class DragField(WindowField):
    direction =0
    keyincrements=ergonomy['dragfield_keyincrements'] #number of times a key must be pressed to cover whole span
    cursorstate='idle'
    showval=1
    focusable=True
    reverse_dir=0 #for things increasing when you go down (e.g. scrollbars)

    def __init__(self,parent,**kwargs):
        self.unit=kwargs.pop('unit',1./ database['floatprecision'])
        self.color=graphic_chart['window_field_bg_idle']
        WindowField.__init__(self,parent,**kwargs)
        self.modimg+=('focus',)
        self.states['focus']=0
        self.minval=0
        self.maxval=1
        dirdict={'h':0,'v':1}
        draw = True
        if isinstance(self.val,float):
            self.maxval=1.0
        else :
            self.maxval = self.val
        for i, j in kwargs.iteritems():
            if i=='draw':
                draw =j
            if i=='color':
                self.color = j
            if i=='maxval':
                self.maxval=j
            if i=='minval':
                self.minval=j
            if i in('dir','direction'):
                self.direction = dirdict.get(j,j)
            if i == 'showval':
                self.showval=j
            if i=='reverse_dir':
                self.reverse_dir=j
        self.group=pgsprite.Group()
        if draw :
            self.redraw()


    def color_mod(self,state,*args):
        if state=='focus':
            return (1.8,1.8,1.8,1)
        return (1,1,1,1)

    def redraw(self,**kwargs):
        self.group.empty()
        color=kwargs.get('color',None)
        if color is None:
            color=self.color
        if len(color)==2:
            if self.direction == 0 :
                self.image.blit(gradients.horizontal(self.rect.size, *color),(0,0))
            else :
                self.image.blit(gradients.vertical(self.rect.size, *color),(0,0))
        else :
            self.image.fill(color)
        cursize=[0,0]
        cursize[self.direction]=kwargs.pop('curlen',graphic_chart['drag_cursor_size'])
        cursize[1-self.direction]=self.rect.size[1-self.direction]
        self.cursor=pgsprite.Sprite(self.group)
        self.cursor.image=pgsurface.Surface(cursize,Canvasflag)
        self.cursor.rect=self.cursor.image.get_rect()
        if array(cursize).all():
            color = graphic_chart['window_decor_fill_color']
            if len(color)==2:
                if self.direction == 0 :
                    self.cursor.image.blit(gradients.horizontal(cursize, *color),(0,0))
                else :
                    self.cursor.image.blit(gradients.vertical(cursize, *color),(0,0))
            else :
                self.cursor.image.fill(color)
            if self.cursorstate=='grabbed':
                self.cursor.image.fill((55,55,155,100))

        self.bg=self.image.copy()
        self.set_val(kwargs.get('val',None))
        self.image.blit(self.bg,(0,0))
        self.image.blit(self.cursor.image,self.cursor.rect.topleft)
        if self.showval:
            self.image.blit(pgu_writen(str(self.val),FONTLIB["base"],graphic_chart['text_color_label']),(0,0))
        self.images['idle']=self.image


    def set_val(self,val=None,rel=None):
        WindowField.set_val(self,val)
        dr = self.direction
        if dr == 0:
            curspos=self.cursor.rect.left
        else :
            curspos=self.cursor.rect.top
        span = self.maxval-self.minval
        size=array(self.rect.size)-array(self.cursor.rect.size)
        if span== 0 :
            return False
        old = curspos
        if rel :
            curspos+=rel[dr]
        else :
            if val is None :
                val = self.val
            else :
                val= min(max(val, self.minval),self.maxval)
            curspos=float(val-self.minval)/span*size[dr]

        if curspos != old and curspos <= size[dr] and curspos>=0.:
            if dr == 0 :
                self.cursor.rect.left=curspos
            else :
                self.cursor.rect.top=curspos
            if rel :
                val = float(curspos)/size[dr]*span + self.minval
                if isinstance(self.maxval,int):
                    val = int(val)
            val=int(val*1./self.unit)*float(self.unit)
            if isinstance(self.unit,int):
                val=int(val)
            self.val= val
            self.image.fill(COLORKEY)
            self.image.blit(self.bg,(0,0))
            self.image.blit(self.cursor.image,self.cursor.rect.topleft)
            if self.showval:
                self.image.blit(pgu_writen(str(self.val),FONTLIB["base"],graphic_chart['text_color_label']),(0,0))
            self.images['idle']=self.image

            return True
        return False

    def event(self,event,**kwargs):
        increment=0
        if self.is_grabbed:
            if self.cursorstate=='idle':
                self.cursorstate='grabbed'
                self.redraw()
            if event.type==pg.MOUSEMOTION :
                self.set_val(None,event.rel)
                return True
            if event.type == pg.MOUSEBUTTONUP:
                self.output()
                user.ungrab()
                self.cursorstate='idle'
                self.redraw()
                return True
        elif event.type == pg.MOUSEBUTTONDOWN :
            if event.button ==1:
                #pg.time.delay(60)
                #evts= pgevent.get((pg.MOUSEMOTION,pg.MOUSEBUTTONUP,pg.MOUSEBUTTONDOWN))
                if self.cursor.rect.collidepoint(self.parent.mousepos(self)) :
                    user.focus_on(self)
                    user.grab(self)
                    return True
                else:
                    self.set_val(None,tuple(array(self.parent.mousepos(self))-array(self.cursor.rect.center)))
                    self.output()
                    return True
            if event.button==4: #wheel up
                increment,direction=1,1
            if event.button ==5: #wheel down
                increment,direction=1,0
        if event.type == pg.KEYDOWN :
            if event.key == pg.K_TAB:
                try:
                    return self.parent.next_field()
                except:
                    return False
            if self.direction=='v':
                if event.key==pg.K_UP:
                    increment,direction=1,1
                if event.key==pg.K_DOWN :
                    increment,direction=1,0
            else:
                if event.key==pg.K_RIGHT :
                    increment,direction=1,1
                if event.key==pg.K_LEFT :
                    increment,direction=1,0
        if increment:
            if self.reverse_dir:
                direction=1-direction
            span = self.maxval-self.minval
            nxt=min(self.val+span/self.keyincrements,self.maxval)
            prv=max(self.val-span/self.keyincrements,self.minval)
            if direction:
                self.set_val(nxt)
            else :
                self.set_val(prv)
            self.output()
            return True
        return False

class GaugeField(WindowField):
    direction =0
    def __init__(self,parent,**kwargs):
        self.bgcolor=graphic_chart['window_field_bg_idle']
        self.color=graphic_chart['window_gauge_fill_color']
        self.remcolor=graphic_chart['window_gauge_rem_color']
        self.negcolor=graphic_chart['window_gauge_neg_color']
        self.negval=0

        WindowField.__init__(self,parent,**kwargs)
        #wid=(self.width,self.height)[1-self.direction]
        self.minval=0
        self.maxval=1
        dirdict={'h':0,'v':1}
        if isinstance(self.val,float):
            self.maxval=1.0
        else :
            self.maxval = self.val
        for i, j in kwargs.iteritems():
            if i=='color':
                self.color = j
            if i=='bgcolor':
                self.bgcolor = j
            if i=='negval':
                self.negval=j
            if i=='maxval':
                self.maxval=j
            if i=='minval':
                self.minval=j
            if i in('dir','direction'):
                self.direction = dirdict.get(j,j)
        self.group=pgsprite.Group()
        self.redraw()

    def redraw(self,**kwargs):
        self.group.empty()
        bgcolor=kwargs.get('bgcolor',self.bgcolor)
        self.bg=self.image.copy()
        self.bg.fill((255,255,255,0))
        if len(bgcolor)==2:
            if self.direction == 0 :
                self.bg.blit(gradients.horizontal(self.rect.size, *bgcolor),(0,0))
            else :
                self.bg.blit(gradients.vertical(self.rect.size, *bgcolor),(0,0))
        else :
            self.bg.fill(bgcolor)
        self.set_val(self.val,True)



    def set_val(self,val=None,force_draw=False,**kwargs):
        WindowField.set_val(self,val)
        negval=kwargs.get('neg',self.negval)
        maxval=kwargs.get('max',self.maxval)
        minval=kwargs.get('min',self.minval)
        vs=(val,negval,maxval,minval)
        svs=(self.val,self.negval,self.maxval,self.minval)
        if vs!=svs or force_draw==True:
            self.val,self.negval,self.maxval,self.minval = vs
            self.image.blit(self.bg,(0,0))
            if self.val<=self.minval:
                return
            if self.negval<self.val:
                fillsize=[0,0]
                ratio =(self.val-self.minval)/(self.maxval-self.minval)
                fillsize[self.direction]=int(self.rect.size[self.direction] *ratio)
                fillsize[1-self.direction]=self.rect.size[1-self.direction]
                self.fill( (0,0), fillsize,kwargs.get('color',self.color))
                if self.negval>0 :
                    fillsize=[0,0]
                    pos=[0,0]
                    oldratio=ratio
                    ratio =min(self.negval/(self.maxval-self.minval),oldratio)
                    fillsize[self.direction]=int(self.rect.size[self.direction] *ratio+1)
                    fillsize[1-self.direction]=self.rect.size[1-self.direction]
                    pos[self.direction]=int(self.rect.size[self.direction] *(oldratio-ratio))
                    self.fill( pos, fillsize,color=kwargs.get('remcolor',self.remcolor))
            else:
                fillsize=[0,0]
                pos=[0,0]
                maxspan =(self.negval-self.val+self.maxval)
                ratio = float(self.negval)/maxspan
                fillsize[self.direction]=int(self.rect.size[self.direction] *ratio+1)
                fillsize[1-self.direction]=self.rect.size[1-self.direction]
                self.fill( (0,0), fillsize,color=kwargs.get('remcolor',self.remcolor))
                ratio = float(self.minval+self.negval-self.val)/maxspan
                fillsize[self.direction]=int(self.rect.size[self.direction] *ratio+1)
                self.fill( (0,0), fillsize,color=kwargs.get('negcolor',self.negcolor))
                fillsize[self.direction]=2
                pos[self.direction]=int(self.rect.size[self.direction] *ratio)
                self.image.fill((255,255,255,50),pgrect.Rect(pos,fillsize), pg.BLEND_RGBA_ADD)

    def fill(self,pos,fillsize,color):
        if not (fillsize[0] and fillsize[1]):
            return False
        if len(color)==2:
            if self.direction == 0 :
                self.image.blit(gradients.horizontal(fillsize, *color),pos)
            else :
                self.image.blit(gradients.vertical(fillsize, *color),pos)
        else :
            self.image.fill(color,pgrect.Rect(pos,fillsize))

class ScrollBar(DragField):
    direction=1
    showval=0
    reverse_dir=1
    def __init__(self,parent,**kwargs):
        super(ScrollBar, self).__init__(parent,**kwargs)



    def redraw(self,**kwargs):
        test= float(self.parent.active_rect.size[self.direction])
        test /= self.parent.maxspan[self.direction]
        test *= self.rect.size[self.direction]
        super(ScrollBar, self).redraw(curlen=int(test))



class ArrowItem(UI_Icon):
    mutable=True
    size=(1,1)
    fixsize=True
    def __init__(self,parent,method,**kwargs):
        super(ArrowItem, self).__init__(**kwargs)
        self.parent=parent
        self.method=method

    def make_surface(self,size,mod,*args,**kwargs):
        return image_load(database['image_path']+graphic_chart['arrow_img'])

    def create(self,*args,**kwargs):
        super(ArrowItem, self).create(*args,**kwargs)
        self.size=self.width,self.height=self.rect.size

    def event(self,event,*args,**kwargs):
        if event.type==pg.MOUSEBUTTONDOWN and event.button==1:
            self.method()
            return True
        return super(ArrowItem, self).event(event,*args,**kwargs)

    def color_mod(self,state,*args):
        if state=='hover':
            return (1.8,1.8,.8,1)
        return (1,1,1,1)


class ListSelField(MultiTextField):
    hoverable=1
    selectable=1
    def event(self,event,*args,**kwargs):
        if event.type == pg.MOUSEBUTTONDOWN and event.button==1 :
            struct= ((str(v),lambda x=v:self.set_val(x,output=1))  for v in self.values )
            user.ui.float_menu(struct)
        else:
            return MultiTextField.event(self,event)

    def set_val(self,val,**kwargs):
        MultiTextField.set_val(self,val)
        if kwargs.get('output',0):
            self.output()

class ArrowList(MultiTextField,UI_Widget):
    _rect=None
    halign='c'
    fixsize=True

    def __init__(self,parent,values,**kwargs):
        self.width,self.height=graphic_chart['window_field_std_size']
        UI_Widget.__init__(self)
        self.direction='h'
        for i,j in kwargs.iteritems():
            if i =='horizontal':
                self.direction='h'
            if i =='vertical':
                self.direction='v'
        self.children=[]
        self.pos={}
        self.selected=None
        self.multiseld=[]
        self.hovering=None
        self.group=pgsprite.Group()
        a1= ArrowItem(self,self.prev_val,set=1,mirrorx=True)
        a2=ArrowItem(self,self.next_val,set=1)

        MultiTextField.__init__(self,parent,values,**kwargs)
        self.children=[a1,a2]
        for c in self.children:
            c.create(self.group)
            c.mutate()
        self.pos[a1]=self.rect.topleft
        self.pos[a2]=tuple(array(self.rect.topright)-array((a2.rect.w,0)))
        self.padding=(self.children[0].width+2,2,self.children[0].width+2,4)

        for c in self.children:
            c.rect.topleft=self.pos[c]
        self.redraw()


    def rm_state(self,state,**kwargs):
        if state=='hover':
                self.unhover()
        return UI_Widget.rm_state(self,state,**kwargs)

    def set_state(self,state,force_redraw=False,**kwargs):
        return UI_Widget.set_state(self,state,force_redraw,**kwargs)

    def redraw(self):
        MultiTextField.redraw(self)
        try:
            a1,a2=self.children
            self.pos[a1]=self.rect.topleft+array((0,(self.rect.h-a1.rect.h)/2))
            self.pos[a2]=tuple(array(self.rect.topright)-array((a2.rect.w,-(self.rect.h-a1.rect.h)/2)))
            self.group.draw(self.image)
        except:
            pass
    def unhover(self):
        if UI_Widget.unhover(self):
            self.redraw()
            return True
        return False

    def hover(self,item):
        if UI_Widget.hover(self,item):
            self.redraw()
            return True
        return False

    def event(self,event):
        if UI_Widget.event(self,event):
            if event.type!=pg.MOUSEMOTION:
                self.redraw()
            user.focus_on(self)
            return True
        if event.type == pg.KEYDOWN :
            if self.direction=='v':
                if event.key==pg.K_DOWN :
                    return self.next_val()
                if event.key==pg.K_UP :
                    return self.prev_val()
            else:
                if event.key==pg.K_RIGHT :
                    return self.next_val()
                if event.key==pg.K_LEFT :
                    return self.prev_val()
        if event.type==pg.MOUSEBUTTONDOWN:
            if event.button==4:
                return self.next_val()
            if event.button==5:
                return self.prev_val()
        return MultiTextField.event(self,event)


class Toggler(ArrowList):
    template_meth=False
    #For potentially evolving templates (given as a method that returns dict or accepts key)

    def __init__(self,parent,templates,container,**kwargs):
        if hasattr(templates,'keys'):
            tmp=templates
        else:
            tmp=templates()
            self.template_meth=1

        vals=sorted(tmp)
        ArrowList.__init__(self,parent,vals,**kwargs)
        self.templates=templates
        self.container=container
        self.contval={}
        self.oldval=None
        self.template=tmp[self.val]

    def get_templates(self):
        if self.template_meth:
            return self.templates()
        else:
            return self.templates

    def output(self,*args,**kwargs):
        tmp=self.get_template()
        if self.template!=tmp:
            self.set_template(tmp,self.oldval)
        ArrowList.output(self,*args,**kwargs)

    #Do something that collect values of the container
    def event(self,*args,**kwargs):
        self.oldval=self.val
        if ArrowList.event(self,*args,**kwargs):
            #the test below is not necessary since output will happen during event
            tmp=self.get_template()
            if set(a[0] for a in self.template)!=set(a[0] for a in tmp):
                self.set_template(tmp,self.oldval)

    def get_template(self,val=None):
        if val is None:
            val=self.val
        if self.template_meth:
            tmp=self.templates(val)
        else:
            tmp=self.templates[val]
        return tmp

    def set_template(self,tmp,oldval=None):
        if tmp==self.template:
            return
        if self.oldval:
            self.contval.setdefault(self.oldval,{})
            for i,j in self.container.fieldict.iteritems():
                if i in set(a[0] for a in self.template) and j:
                    self.contval[self.oldval][i]=j.val
        self.container.clear()
        tempval=()
        for j in sorted(tmp):
            i=j[0]
            if hasattr(j[-1],'keys'):
                t=j[:-1]+({} ,)
                t[-1].update(j[-1])
            else:
                t=j[:]+({} ,)
            t[-1]['extfield']=1
            if self.val in self.contval and i in self.contval[self.val]:
                t[-1]['val']=self.contval[self.val][i]
            tempval+= t,
        self.template=tempval
        self.container.parse(tempval)
        self.container.update()
        if self.val in self.contval:
            for i,j in self.contval[self.val].iteritems():
                #if i in self.container.fieldict:
                    self.container.fieldict[i].set_val(j)


class ColorField(WindowField):
    #Choose among a list of colors
    colors=['r','g','b','m','c','y']
    def __init__(self,parent,**kwargs):
        WindowField.__init__(self,parent,**kwargs)
        for i,j in kwargs.iteritems():
            if i in ('colors','col') :
                self.colors = j

        self.set_val(0)


    def set_val(self,val=0):
        if val != self.val :
            WindowField.set_val(self,val)
            try:
                val=val%len(self.colors)
                color=self.colors[val]
            except:
                color=val
                if not color in self.colors:
                    if not hasattr(color,'__iter__'):
                        try:
                            try:
                                color=tuple(int(i *255) for i in colorconverter.to_rgba(color))
                            except:
                                color=eval(color)
                                if True in [0.<i<1. for i in color]:
                                    color = tuple( int(i*255)%256 for i in color)
                                if len(color)==3:
                                    color+=255,
                            self.colors=list(self.colors)
                            self.colors.append(color)
                        except:
                            print 'Unknown color'
                            color=self.colors[0]
            self.val=color

            col2=array(color)
            col2[:3]*=.8
            self.image.blit(gradients.horizontal(self.rect.size, color,col2),(0,0))


    def event(self,event,**kwargs):
        if event.type == pg.MOUSEBUTTONDOWN:
            dif=1
            if event.button ==5 :
                dif=-1
            if event.button in (1,4,5):
                try:
                    self.set_val( self.colors.index(self.val)+dif)
                except:
                    pass
                self.output()
                return True
            if event.button ==3 :
                #Right click: allows to add a new color
                user.ui.input_menu('input',self.set_val,title='Add color:')
        return False
