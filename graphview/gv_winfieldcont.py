# -*- coding: utf-8 -*-
from gv_winfields2 import *

"""#test for a glitch that will hopefully be corrected lated in pygame
testsurface=pg.surface.Surface((10,10))
testrect=pg.rect.Rect((2,2,4,4))
testsubsurface=testsurface.subsurface(testrect)
if testsubsurface.get_rect()!=testrect :
    pgrectglitch=True
else :
    pgrectglitch=False """

class FieldContainer(UI_Widget):
    fixsize=False
    col_align=True # alignment of items into proper columns
    active_surf=None
    interspace=4 #space between fields
    margin=4

    scrollable=False
    _maxsize=False
    _minsize=False
    maxspan=None

    output_method=None
    def __init__(self,parent,*args,**kwargs):
        self.table={}#table for true fields
        self.fieldict={}#if fields are named for ulterior access
        self.decor=[]#list of annex fields such as scrollbars
        self.offset=[0,0] #for scrolling
        self.newfields=[]
        self.multispan={} #for the fields that may span multiple rows or colums
        self.halign=sparse('l')
        self.valign=sparse('t')
        UI_Widget.__init__(self,*args,parent=parent,**kwargs)
        self.size=list(kwargs.get('size',(2*self.margin,2*self.margin)))
        for i,j in kwargs.iteritems():
            if i=='fixsize':
                self.fixsize=j
            if i=='margin':
                self.margin = j
            if i=='scrollable':
                self.scrollable=j
            if i in ('w','wid','width'):
                self.size[0]=int(j)
            if i in ('h','hei','height'):
                self.size[1]=int(j)
            if i=='maxsize':
                self._maxsize=tuple(int(x) for x in j)
            if i=='minsize':
                self._minsize=tuple(int(x) for x in j)

        self.group=pg.sprite.Group()
        self.decorgroup=pg.sprite.Group()
        self.image=pg.surface.Surface(self.size,pg.SRCALPHA)
        self.image.fill((0,0,0,0))
        if self.scrollable :
            self.yscrollbar=None
            self.xscrollbar=None
        self.rect=self.image.get_rect()
        self.parse(kwargs.get('struct',None))

    def kill(self,recursive=True):
        UI_Widget.kill(self,recursive)
## -------------------  Size related ---------------------------------------------
    @property
    def width(self):
        return self.rect.w
    @property
    def height (self):
        return self.rect.h

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self,val):
        self._dirty=val
        if val:
            try:
                self.parent.dirty=1
            except:
                pass

    @width.setter
    def width(self,val):
        self.size[0]=val
        if val != self.size[0]:
            self.compute_pos()
    @height.setter
    def height (self,val):
        self.size[1]=val
        if val != self.size[1]:
            self.compute_pos()

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self,val):
        self._rect=val
        self.rect_update()

    def rect_update(self):
        val=self.rect
        act=array(val.size)- array(self.mrg()[2:])
        act = tuple(max(0,i) for i in act)
        self.active_rect=pgrect.Rect(self.mrg(False)[:2],act)
        #if pgrectglitch :
        #    self.active_surf=self.image.subsurface(pgrect.Rect(self.active_rect.topleft,act-array(self.active_rect.topleft)))
        #else :
        self.active_surf=self.image.subsurface(self.active_rect)

    def mrg(self,sizeonly=True):
        mg=[self.margin for i in xrange(4)]
        if self.scrollable :
            if self.yscrollbar in self.decorgroup :
                mg[2]+=self.yscrollbar.rect.w
            if self.xscrollbar  in self.decorgroup  :
                mg[3]+=self.xscrollbar.rect.h
        if sizeonly :
            mg[2]+=mg[0]
            mg[3]+=mg[1]
            mg[0]=mg[1]=0

        return mg

    @property
    def maxsize(self):
        size= None
        if self.fixsize and not self.fixsize in ('v','h'):
            return self.size
        elif self._maxsize:
            size= self._maxsize
        if size is None:
            try :
                size= self.parent.maxsize
            except:
                size= self.parent.rect.size
        if self.fixsize:
            if self.fixsize=='v':
                return (size[0],self.size[1])
            else:
                return (self.size[0],size[1])
        return size


    @property
    def minsize(self):
        size=None
        if self.fixsize and not self.fixsize in ('v','h'):
            return self.size
        elif self._minsize:
            size= self._minsize
        elif self.maxspan:
            w = min(self.maxsize[0],self.maxspan[0]+self.mrg()[2] )
            h = min(self.maxsize[1],self.maxspan[1]+self.mrg()[3] )
            size= (w,h)
        if size is None:
            size= self.mrg()[2:]
        if self.fixsize:
            if self.fixsize=='v':
                return (size[0],self.size[1])
            else:
                return (self.size[0],size[1])
        return size


    def resize(self,size,external=True):
        self.dirty=1
        w=max(min(self.maxsize[0],size[0]),self.minsize[0])
        h=max(min(self.maxsize[1],size[1]),self.minsize[1])
        self.size=(w,h)
        self._image=pg.surface.Surface((w,h),pg.SRCALPHA)
        self.rect=pg.rect.Rect(self.rect.topleft,(w,h))
        self.images['idle']=self._image
        if external :
            #when resized by some external force
            self.compute_pos()


## -------------------  Image related ---------------------------------------------

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self,val):
        self._image=val
        if self.active_surf :
            self.rect_update()

    def draw(self,bg=None):
#        self.image = pg.surface.Surface(self.image.get_rect().size,pg.SRCALPHA)
#        self.rect = self.image.get_rect()

        if not self.dirty :
            return False
        #print self, pg.time.get_ticks()

        self.image=pg.surface.Surface(self.size,pg.SRCALPHA)
        self.image.fill((0,0,0,0))
        if not bg:
            try:
                bg=self.bg
            except:
                pass
        if bg :
            self.image.blit(bg.convert(self.image),(0,0))
        self.group.update()
        for c in self.children :
            if c in self.pos :
                pos=array(self.pos[c])
                if not c in self.decor :
                    pos-=array(self.offset)
                    c.rect.topleft = pos

            if hasattr(c,'draw'):
                #c.dirty=1
                c.draw()
        self.group.draw(self.active_surf)
        self.decorgroup.draw(self.image)

#         = self.image.convert()
#        test.set_alpha(180)
#        screen.blit(test,(0,0))
#        test.blit(self.image,(0,0))
        if not self.per_pixel_alpha and ( not self.parent or
                not hasattr(self.parent,'alpha')) : # if not further alpha blitting
            #self.image=self.image.convert_alpha()
            self.image=self.image.convert()
            self.image.set_colorkey(COLORKEY)
        self.images['idle']=self.image
        self.set_image(self.state)
        self.dirty=0


## -------------------  Event related ---------------------------------------------

    def update(self):
        #for i, j in self.pos.iteritems():
        #    i.rect.topleft=j
        #    i.update()
        if self.catch_new():
            return True
        for c in self.children :
#            c.rect.topleft=tuple(array(self.rect.topleft)+array(self.pos[c]))
            c.update()
        if UI_Widget.update(self):
            self.dirty=1

    def abspos(self,child=None,**kwargs):
        if child :
            mod = array(self.pos.get(child,(0,0)))
            if not child in self.decor :
                mod+=array(self.active_rect.topleft)
                if kwargs.get('with_offset',1):
                    mod-= self.offset
            if self.parent :
                return tuple(array(self.parent.abspos(self))+mod)
            else :
                return tuple(array(self.rect.topleft)+mod)
        else :
            if self.parent :
                return self.parent.abspos(self)
            else :
                return self.rect.topleft

    def event(self,*args,**kwargs):
        kwargs.setdefault('children',[c for c in self.children if not c in self.decor] )
        if UI_Widget.event(self,*args,**kwargs) :
            self.draw()
            return True
        elif self.decor and UI_Widget.event(self,*args,refpos=self.abspos(),children=self.decor) :
            self.draw()
            user.focus_on(self)
            return True
        event= args[0]
        if self.scrollable:
            delta=ergonomy['key_graph_move_rate']
            if event.type in ( pg.KEYDOWN, pg.MOUSEBUTTONDOWN) :
                self.dirty=1
            if event.type == pg.KEYDOWN :
                if event.key==pg.K_DOWN :
                    return self.set_offset(delta,1,True)
                if event.key==pg.K_UP :
                    return self.set_offset(-delta,1,True)
                if event.key==pg.K_RIGHT :
                    return self.set_offset(delta,0,True)
                if event.key==pg.K_LEFT :
                    return self.set_offset(-delta,0,True)
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button==5 :
                    return self.set_offset(delta,1,True)
                if event.button==4 :
                    return self.set_offset(-delta,1,True)
        return False


    def set_command(self,*args,**kwargs):
        if self.parent :
            return self.parent.set_command(*args,**kwargs)
        else :
            print self, 'receives set command and cannot forward it.'
            return False

    def rem_command(self,*args,**kwargs):
        if self.parent :
            return self.parent.rem_command(*args,**kwargs)
        else :
            print self, 'receives rem command and cannot forward it.'
            return False

    def exe_command(self,*args,**kwargs):
        if self.parent :
            return self.parent.exe_command(*args,**kwargs)
        else :
            print self, 'receives exe command and cannot forward it.'
            return False


    def rem_from_queue(self,source):
        if self.parent:
            return self.parent.rem_from_queue(source)
        else :
            print self, 'receives rem command and cannot forward it.'
            return False

## -------------------  Field related ---------------------------------------------

    def next_field(self):
        focus=user.focused_on
        idx=None
        for x in sorted(self.table):
            for y in sorted(self.table[x]):
                if self.table[x][y]==focus:
                    x0,y0,idx=x,y,self.children.index(focus)
                elif idx:
                    try:
                        if self.table[x][y].focusable:
                            return user.focus_on(self.table[x][y])
                    except:
                        pass
        if not idx:
            return None
        for y in range(y0):
            for x in sorted(self.table):
                try:
                    if self.table[x][y].focusable:
                        return user.focus_on(self.table[x][y])
                except:
                    pass

    def parse(self,struct):
        #simple parsing for menus
        if not struct:
            return False
        for line in struct :
            if isinstance(line[0],basestring) and isinstance(line[1],basestring):
                self.parse_ext((line,) ,renewdict=False)
                continue
            else :
                gnr='text'
            field=self.add(gnr,val=line[0],output_method=line[1],
                selectable=True,no_paint=True)
            if gnr =='text' and len(line)>2:
                field.status_tip=line[2]
        self.update()

    def parse_ext(self,struct,**kwargs):
        #extended parsing for general windows
        preval={}
        for i,j in self.fieldict.iteritems():
            if j:
                preval[i]=j.val
        if kwargs.get('renewdict',True):
            self.fieldict={}
        for a in struct:
            attr=a[0]
            typ=a[1]
            try:
                opts=a[2]
            except:
                opts={}
            val=opts.pop('val',preval.get(attr,None))
            if val is None:
                if 'values' in opts:
                    val=opts['values'][0]
                elif typ=='text':
                    val=attr
            if 'legend' in opts:
                self.add('text',val=opts['legend'],no_paint=True)

            tmp=self.add(typ,val=val,no_paint=True,**opts)
            if 'bind' in opts: #Is this redundant with output_method?
                tmp.bind_command(opts['bind'])
            if 'tip' in opts:
                tmp.status_tip=opts['tip']
            self.fieldict[attr]=tmp

    def drop_menu(self,anchor,struct,**kwargs):
        menu=DropMenu(self,anchor,struct=struct,**kwargs)
        self.group.add(menu)
        user.ui.float_menu(struct)
        print 'Incomplete drop field'
        #TODO: Drop field (for choices inside containers with Fieldlist,
            #not just for statusbar menu)

    def add(self,field,**kwargs):
        if field in self.children :
            return False
        kwargs.pop('no_paint',False) #Option for windows:do not update graphics
        if isinstance(field,basestring):
            if field == 'input':
                field=InputField(self,**kwargs)
            elif field=='icon':
                field=IconField(self,**kwargs)
            elif field=='array':
                field=ArrayInputField(self,**kwargs)
            elif field =='text' :
                field = TextField(self,**kwargs)
            elif field=='arrowsel':
                field = ArrowList(self,kwargs.pop('values'),**kwargs)
            elif field=='extsel':
                field = ExtSelField(self,**kwargs)
            elif field=='listsel':
                field = ListSelField(self,**kwargs)
            elif field =='list' :
                val=kwargs.pop('val',None)
                field = FieldList(self,val, **kwargs)
            elif field =='inputlist' :
                val=kwargs.pop('val',None)
                field = InputList(self,val, **kwargs)
            elif field == 'drag':
                field =DragField(self,**kwargs)
            elif field == 'blank':
                field =WindowField(self,**kwargs)
            elif field == 'gauge':
                field=GaugeField(self,**kwargs)
            elif field == 'color':
                field=ColorField(self,**kwargs)
            elif field == 'okbutton':
                kwargs['output_method']='confirm'
                field=TextField(self,**kwargs)
                field.set_state('disabled')
                self.set_command('emptyqueue',(lambda e=field:e.set_state('disabled'),()))
                self.set_command('queue',(lambda e=field:e.rm_state('disabled'),()))
            elif field == 'toggle':
                ckwargs={}
                ckwargs.update(kwargs)
                if not 'width' in kwargs and not 'size' in kwargs and not 'minsize' in kwargs:
                    ckwargs['width']=graphic_chart['window_field_std_size']
                if 'pos' in kwargs:
                    pos=kwargs['pos']
                    ckwargs['pos']=(pos[0]+2,pos[1])
                cont = self.add(FieldContainer(self),**ckwargs)
                field=Toggler(self,kwargs.pop('templates'),cont,**kwargs)
                tmp=field.get_templates()
                if 'val' in kwargs and kwargs['val'] in tmp:
                    cont.parse_ext(tmp[kwargs['val']])
                else:
                    cont.parse_ext(tmp[sorted(tmp)[0]])
                field.bind_command(lambda s=self:s.update())
            elif field=='dropmenu':
                val=kwargs.pop('val',None)
                field=TextField(self,val=val[0],**kwargs)
                field.bind_command(lambda f=field,v=val[1],kw=kwargs:self.drop_menu(f,v,**kw))
            else :
                print 'FieldContainer error : bad Winfield type'
                return
        elif type(field).__name__=='classobj':
            field=field(self,**kwargs)

        tabdim=(max([-1]+self.table.keys()) , max([-1]+[max(j.keys()) for j in self.table.values()] )   )
        pos=kwargs.get('pos',(tabdim[1]+1,0))
        pos=(pos[1],pos[0]) ### IMPORTANT: easy source of confusion
        if pos[0]<0:
            pos=(pos[0]+1+tabdim[0], pos[1])
        if pos[1]<0:
            pos=(pos[0],pos[1]+1+tabdim[1])
        x=pos[0]
        y=pos[1]
        if not x in self.table:
            self.table[x]={}
        if y in self.table[x]:
            dep=[]
            for xx in self.table:
                if xx in self.table and y in self.table[xx]:
                    if xx>=x:
                        dep.append(self.table[xx][y])
            xx=x+1
            while dep:
                if not xx in self.table:
                    self.table[xx]={}
                self.table[xx][y]=dep.pop(0)
                xx+=1

        self.table[x][y]=field
        if 'key' in kwargs:
            self.fieldict[kwargs.get('key')]=field
        #else:
            #self.fieldict[(x,y)]=field

        if 'colspan' in kwargs:
            sp = kwargs['colspan']
            self.multispan[field]={'col':sp}
            for i in xrange(sp-1):
                try:
                    self.table[x+i+1][y]=None
                except:
                    pass

        if 'rowspan' in kwargs:
            sp = kwargs['rowspan']
            self.multispan[field]=self.multispan.get(field,{})
            self.multispan[field]['row']=sp
            for i in xrange(sp-1):
                try:
                    self.table[x][y+i+1]=None
                except:
                    pass
        try:
            self.halign[field]=kwargs['halign']
        except:pass
        try:
            self.valign[field]=kwargs['valign']
        except:pass


        field.parent=self
        self.children.append(field)

        self.group.add(field)
        self.newfields.append(field)
        return field

    def remove(self,field):
        self.children.remove(field)
        self.group.remove(field)
        ml=self.multispan
        for x in self.table :
            for y in self.table[x]:
                if self.table[x][y]==field:
                    del self.table[x][y]
                    if field in ml and 'row' in ml[field]:
                        for i in xrange(ml[field]['row']-1):
                            del self.table[x+i][y]
                    if field in ml and 'col' in ml[field]:
                        for i in xrange(ml[field]['col']-1):
                            del self.table[x][y+i]
        for i in sorted(self.fieldict):
            if self.fieldict[i]==field:
                del self.fieldict[i]
        self.compute_pos()

    def clear(self):
        [c.kill(True) for c in self.children]
        self.children=[]
        self.group.empty()
        self.table={}
        self.fieldict={}
        self.compute_pos()

    def catch_new(self):
        if self.newfields:
            self.newfields=[]
            self.compute_pos()
            return True
        return False

    def field_maxsize(self):
        #NB: possible amelioration: pass field as parameter and
        #look up its position in table to adjust by row and column
        if self.maxsize:
            return tuple(int(x) for x in self.maxsize-array(self.mrg()[2:]))
        else:
            return None

    def compute_pos(self,margin=None,active_rect=None):
        self.dirty=1
        multisp=None
        if not active_rect :
            try :
                active_rect = self.active_rect
            except :

                active_rect=self.rect

        sizebefore=active_rect.size
        #print self.table
        if not self.table :
            return False
        tabdim=(max(self.table.keys())+1, max(max(j.keys()) for j in self.table.values() )+1)
        col_width=[0 for x in range(tabdim[0])]
        row_height=[0 for y in range(tabdim[1])]
        resizable_cols=[]
        resizable_rows=[]
        largest={} #largest element of each row or column
        isp=self.interspace

        #First run: minsizes and interspace
        for x in range(tabdim[0]) :
            for y in range(tabdim[1]):
                i=self.table.get(x,{}).get(y,False)
                if i:
                    iw,ih=i.minsize
                        #if hasattr(i,'maxspan') and i.children : #if i is a container itself
                        #    iw,ih=(min(i.rect.size[z],(array(i.maxspan)+array(i.mrg()[2:]))[z]) for z in (0,1))
                    if (i.fixsize=='v' or not i.fixsize ) and not x in resizable_cols :
                            resizable_cols.append(x)
                    if (i.fixsize=='h' or not i.fixsize ) and not y in resizable_rows :
                            resizable_rows.append(y)
                    xs,ys=x,y
                    if i in self.multispan:
                        multisp
                        if 'col' in self.multispan[i]:
                            xs+= self.multispan[i]['col']-1
                            xs=min(xs,tabdim[0])
                        if 'row' in self.multispan[i]:
                            ys+= self.multispan[i]['row']-1
                            ys=min(ys,tabdim[1])
                    if iw > col_width[xs]:
                        col_width[xs]=iw+isp
                        largest[(xs,0)]=i
                    if ih > row_height[ys] :
                        row_height[ys]=  ih+isp
                        largest[(0,ys)]=i
        width=sum(col_width) #+( len(col_width)-1)*isp
        height= sum(row_height) #+( len(row_height)-1)*isp
        # If either width or height in excess, add scrollbar
        # (which enlarges margins, so do this before any reference to margins)
        if self.scrollable :
            if self.scrollable=='v':
                possible=(0,1)
            elif self.scrollable=='h':
                possible=(1,0)
            else :
                possible=(1,1)
            bars=('xscrollbar','yscrollbar')
            for i in (0,1):
                bar=bars[i]
                field = getattr(self,bar)
                dif =-self.active_rect.size[i]+ (width,height)[i]
                if dif>0  and possible[i]:
                    if field:
                        continue
                    size=[0,0]
                    size[i]=self.active_rect.size[i]
                    size[1-i]=graphic_chart['scrollbar_size']
                    widget=ScrollBar(
                            self,dir=i,val=self.offset[i],
                            maxval=dif,h=size[1],w=size[0],
                            draw=False)
                    setattr(self,bar,widget)
                    widget.bind_command(lambda v,drc=i,e=self:e.set_offset(v,drc))
                    widget.bind_command('do')
                    field = getattr(self,bar)
                    if not field in self.decor:
                        self.decor.append(field)
                    if not field in self.children :
                        self.children.append(field)
                        self.decorgroup.add(field)
                        self.rect_update()
                elif field :
                    if field in self.children :
                        self.children.remove(field)
                        self.decorgroup.remove(field)
                        self.rect_update()
                    if field in self.decor:
                        self.decor.remove(field)
        #Grow to expected size (either given by user or suggested by parent)
        expw=self.size[0]-self.mrg()[2]
        #exph=self.size[1]-self.mrg()[3]
        exph=0
        if width < expw :
            dif = expw-width
            resc= sorted(resizable_cols)
            while dif >0 and resc :
                c=resc[-1]
                if col_width[c] > dif/len(resc):
                    resc.remove(c)
                else :
                    for c in resc :
                        col_width[c]=dif/len(resc)
                    dif=0
            width=expw
        if height < exph:
            dif =exph-height
            resr= sorted(resizable_rows)
            while dif >0 and resr :
                r=resr[-1]
                if row_height[r] > dif/len(resr):
                    resr.remove(r)
                else :
                    for r in resr :
                        row_height[r]=dif/len(resr)
                    dif=0
            height=exph

        #Second run: resize, position and alignment
        for x in range(tabdim[0]) :
            for y in range(tabdim[1]):
                it = self.table.get(x,{}).get(y,False)
                if it:
                    it = self.table[x][y]
                    if not it.fixsize:
                        size=array((col_width[x]-isp,row_height[y]-isp))
                        if it in self.multispan:
                            sp =self.multispan[it].get('col',1)
                            for i in xrange(sp-1):
                                try:
                                    size[0]+=col_width[x+i+1]+isp
                                except:
                                    pass
                            sp =self.multispan[it].get('row',1)
                            for i in xrange(sp-1):
                                try:
                                    size[0]+=row_height[y+i+1]+isp
                                except:
                                    pass

                        #it._maxsize=size
                        if tuple(size) !=(it.width, it.height):
                            it.resize(size)
                    else :
                        size= it.minsize

                    posx=sum(col_width[:x])
                    posy=sum(row_height[:y])
                    #if not self.col_align :
                    #    posx=sum( self.table[xx][y].minsize[0] for xx in range(x) )

                    if self.halign[it]=='r':
                        posx+=col_width[x]-isp-size[0]
                    elif self.halign[it]=='c':
                        posx+=(col_width[x]-isp-size[0])/2

                    if self.valign[it]=='b':
                        posx+=row_height[x]-isp-size[1]
                    elif self.valign[it]=='c':
                        posx+=(row_height[x]-isp-size[1])/2

                    self.pos[it]=[posx,posy]

        #give final size to this container
        self.maxspan=(width,height)
        self.resize(self.maxspan,False)
        # Adjust offset and span of previously added scrollbars
        if self.scrollable :
            if self.scrollable=='v':
                possible=(0,1)
            elif self.scrollable=='h':
                possible=(1,0)
            else :
                possible=(1,1)
            bars=('xscrollbar','yscrollbar')
            for i in (0,1):
                bar=bars[i]
                field = getattr(self,bar)
                dif =-self.active_rect.size[i]+ self.maxspan[i]
                if dif>0 and field and possible[i]:
                    size=[0,0]
                    size[i]=self.active_rect.size[i]
                    size[1-i]=graphic_chart['scrollbar_size']
                    field.maxval=dif
                    field.resize(size)
                    field.set_val(self.offset[i])
                    field.redraw()
                    if i==0:
                        field.rect.topleft=self.active_rect.bottomleft
                    else :
                        field.rect.topleft=self.active_rect.topright
                    self.pos[field]=field.rect.topleft
                    #field.bind_command(lambda v,drc=i,e=self:e.set_offset(v,drc))
                    if not field in self.children:
                        self.children.append(field)
                        self.decorgroup.add(field)
                        self.decor.append(field)
                else :
                    if field in self.children :
                        self.children.remove(field)
                        self.decorgroup.remove(field)
                        self.rect_update()
                    if field in self.decor:
                        self.decor.remove(field)

        self.update()
        if self.parent and hasattr(self.parent,'newfields'):
            #renew parent layout too
            if sizebefore != self.active_rect.size and not self in self.parent.newfields:
                self.parent.newfields.append(self)
        #print self, self.minsize, self.width, self.height, self.rect, self.active_rect, self.maxspan, sizebefore


        #if isinstance(margin,int):
            #lmargin,tmargin,rmargin,bmargin=tuple(margin for i in xrange(4))
        #else :
            #if not margin :
                #margin= self.mrg(False)
            #if len(margin)==2 :
                #lmargin,tmargin=0,0
                #rmargin,bmargin=margin
            #elif len(margin)==4 :
                #lmargin,tmargin,rmargin,bmargin=margin


    def set_offset(self,offset,dr=None,additive=False):
        bars = (self.xscrollbar,self.yscrollbar )
        if dr==None :
            if additive :
                offset += self.offset
            self.offset=offset
            for bar in bars:
                bar.redraw()
        else :
            maxoff = self.maxspan[dr]-self.active_rect.size[dr]
            if maxoff <1:
                return False
            if offset == 'max':
                offset = maxoff-1
            if additive :
                offset += self.offset[dr]
            if offset >0:
                self.offset[dr]=min(offset,maxoff)
            else :
                self.offset[dr]=max(offset,0)
            bar=bars[dr]
            if bar and bar.val != offset :
                bar.set_val(offset)

        self.draw()
        return True


    def bind_command(self,method,vals=None,**kwargs):
        if vals == None :
            vals=()
        else :
            if not hasattr(vals,'__iter__'):
                vals=[vals]
            else :
                vals = list(vals)

        if hasattr(method,'__iter__'):
            for i in method:
                if vals :
                    val = vals.pop(0)
                else :
                    val=None
                self.bind_command(i,val)
        elif isinstance(method,basestring):
            self.parent.set_command(self,method,**kwargs)
        else :
            self.parent.set_command(self, (method,tuple(vals)),**kwargs)

    def unbind_command(self,method=None):
        self.parent.rem_command(self,method)


class DropMenu(FieldContainer):

    def __init__(self,parent,anchor,**kwargs):
        FieldContainer.__init__(self,parent,**kwargs)
        self.anchor=anchor
        adir=self.anchordir=kwargs.get('dir','d')
        self.parent.pos[self]=self.parent.pos[self.anchor]

        if  adir=='d':
            self.parent.pos[self]+=array((0,0))

class ArrayInputField(FieldContainer):

    def __init__(self,parent,**kwargs):
        self.length=length=kwargs.pop('length',1)
        FieldContainer.__init__(self,parent,**kwargs)
        typ=kwargs.get('typecast',str)
        self.val=[typ() for i in range(length)]
        self.fields=[]
        kwargs.setdefault('width',graphic_chart['window_field_std_size'][0] )
        kwargs['width']=kwargs['width']/self.length-self.interspace
        for i in range(length):
            #kwargs['output_method']=lambda e,key=i:self.set_fval(key,e)
            kwargs['pos']=(0,i)
            kwargs['val']=self.val[i]
            self.fields.append(self.add('input', **kwargs))

    def exe_command(self,field,val):
        return self.set_fval( self.fields.index(field),val[0])

    def set_fval(self,key,val):
        if self.val[key]!=val:
            self.val[key]=val
            self.output()

    def set_val(self,val):
        if val is self.val:
            return False
        if hasattr(val,'__iter__'):
            for i in range(min(len(val),self.length) ):
                self.val[i]=val[i]
                self.fields[i].set_val(val[i])
            return True
        else:
            return False

    def output(self,val=None):
        if val is None:
            val = array( self.val )
        if self.output_method:
            self.output_method( val )
        else:
            #cProfile.runctx('self.parent.exe_command(self,val=(val,) )',globals(),locals(),
                #database['basepath']+'profile.dat')
            self.parent.exe_command(self,val=(val,) )
        self.unselect()




class FieldList(FieldContainer):
    #Can be used in two ways: passive fields or active fields
    #In the first case, clicking on one field sets it as the value of the fieldlist
    # and the fieldlist is given as a list of (field_label,field_value)
    #In the second case, clicking on one fields starts its own method
    #  and the fieldlist is given as a list of (field_label,field_method)
    #  or (field_label,field_vaue,field_methdod)

    selectable=True
    scrollable=True
    def __init__(self,parent,flist,**kwargs):
        FieldContainer.__init__(self,parent,**kwargs)
        self.direction='v'
        self.output_method='confirm'
        for i,j in kwargs.iteritems():
            if i =='output_method' :
                self.output_method = j
            if i =='horizontal':
                self.direction='h'
            if i=='selectable':
                self.selectable=j
        self.active_fields=kwargs.get('active',False)
        self.set_list(flist)

    def set_list(self,flist):
        self.table={}
        self.fieldict={}
        for c in self.children :
            c.kill()
        self.children=[]
        self.newfields=[]
        self.fieldlist=[]
        self.val=None
        self.selected=None
        self.valdict={}
        self.methdict={}
        j=0
        for j,i in enumerate(flist) :
            if self.direction=='h' :
                pos=(0,j)
            else :
                pos=(j,0)
            tmp=self.add(TextField(self,val=str(i[0]),selectable=True),pos=pos)
            self.fieldlist.append(tmp)
            self.valdict[tmp]=i[1]
            if self.active_fields:
                self.methdict[tmp]=i[-1]
                if hasattr(i[-1],'__iter__'):
                    tmp.bind_command(i[-1][0],i[-1][1])
                else:
                    tmp.bind_command(i[-1])
        self.update()

    @property
    def vallist(self):
        return [self.valdict[t] for t in self.fieldlist]

    def draw(self,*args):
        self.bg =pgsurface.Surface(self.rect.size,pg.SRCALPHA)
        self.bg.fill(graphic_chart['window_field_bg_idle'])
        return FieldContainer.draw(self,self.bg)

    def select(self,item):
        if not self.selectable :
            return True
        FieldContainer.select(self,item)
        if self.selected :
            self.val=self.valdict[self.selected]
            if not self.active_fields:
                if isinstance(self.output_method,basestring):
                    self.parent.set_command(self,self.output_method)
                else :
                    self.parent.set_command(self,(self.output_method,(self.val,) ))
            else :
                self.parent.set_command(self,self.output_method)
            self.parent.exe_command(self)
            #self.unselect()
        else :
            self.val = None
            self.parent.rem_from_queue(self)
            self.parent.set_command(self,(None,))

    def add_field(self,field):
        self.flist


class InputList(FieldList):
    # A list representing a series of items
    # Upon selecting one of them, a floating menu is loaded
    # Upon exiting the menu, the list sends out its new value through output method
    def __init__(self,parent,flist,**kwargs):
        self.opts=kwargs.pop('opts',{'type':'input'}) #multiple types allowed
        self.extensible=kwargs.pop('add',False)
        self.unique=kwargs.pop('unique',False) #if new field==existing field, discard it
        self.sendall=kwargs.pop('sendall',True)
        self.clip=None
        FieldList.__init__(self,parent,flist,**kwargs)

    def select(self,item):
        if not self.selectable :
            return True
        FieldContainer.select(self,item)
        if self.selected :
            self.val=self.valdict[self.selected]
            self.input_menu(self.selected)
        else :
            self.val = None
            self.parent.rem_from_queue(self)
            self.parent.set_command(self,(None,))

    def unselect(self):
        FieldList.unselect(self)
        self.val = None
        self.dirty=1 #Why do I need this?

    def event(self,event,*args,**kwargs):
        if self.extensible and event.type==pg.MOUSEBUTTONUP and event.button==3:
            struct= ()
            if self.hovering and self.hovering.val != 'None':
                if not self.unique:
                    struct+=(
                        ('Duplicate',lambda e=self.hovering: self.dupl_field(e) ),)
                struct +=(
                    #('Insert',lambda e=self.hovering: self.insert_field(e) ),
                    ('Delete',lambda e=self.hovering: self.remove_field(e) ) ,
                    ('Cut',lambda e=self.hovering: self.cut(e) ), )
            else:
                if hasattr(self.opts['type'],'__iter__'):
                    for t in self.opts['type']:
                        kwargs={'type':t}
                        if self.hovering:
                            func=lambda e=self.hovering,kw=kwargs:self.input_menu(e,**kw)
                        else:
                            func=lambda kw=kwargs: self.input_menu('None',**kw)
                        if hasattr(t,'__iter__'):
                            struct +=  ('Add {}'.format(t[1]),func),
                        else:
                            struct +=  ('Add {}'.format(t),func),
                else:
                    if self.hovering:
                        func=lambda e=self.hovering,kw=kwargs:self.input_menu(e,**kw)
                    else:
                        func=lambda kw=kwargs: self.input_menu('None',**kw)
                    struct +=  ('Add',func),
            if self.clip:
                struct+=(
                 ('Paste',lambda e=len(self.fieldlist),c=self.clip: self.paste(c,e) ),
                 )
            user.ui.float_menu( struct,parent_window=self.parent )
            #self.input_menu('None')
            return True
        if self.extensible and self.hovering and self.hovering.val != 'None':
            if event.type==pg.KEYUP:
                pos=self.fieldlist.index(self.hovering)
                if event.key==pg.K_UP:
                    return self.paste(self.hovering,e)
                if event.key==pg.K_DOWN:
                    return self.paste(self.hovering,e+1)
        return FieldList.event(self,event,*args,**kwargs)

    def output(self,val=None):
        if not val :
            self.output_method(self.vallist)
        else:
            self.output_method(( val, ) )
        self.unselect()



    def remove_field(self,field):
        if field in self.fieldlist:
            self.fieldlist.remove(field)
        for dic in (self.valdict, self.methdict):
            try:
                del dic[field]
            except:
                pass
        flist= [(i.val,self.valdict[i]) for i in self.fieldlist  ]
        self.set_list(flist)
        self.output()

    def dupl_field(self,field):
        if not field in self.valdict:
            return False
        flist= [(i.val,self.valdict[i]) for i in self.fieldlist  ]
        copy= shallow_nested(self.valdict[field],1)
        flist.insert(self.fieldlist.index(field)+1,(field.val, copy))
        self.set_list(flist)
        self.output()

    def insert_field(self,key,field,idx):
        #if not field in self.valdict:
            #return False
        flist= [(i.val,self.valdict[i]) for i in self.fieldlist  ]
        #idx=self.fieldlist.index(field)
        if self.unique and True in [key==f[0] for f in flist]:
            return False
        flist.insert(idx,(key,field  ))
        self.set_list(flist)
        #self.input_menu(self.fieldlist[idx] )


    def changevals(self,e,item,key):
        if hasattr(self.val,'__iter__'):
            meth=lambda e,k=key,s=item: self.valdict.update({s:(k,e) })
        else:
            meth=lambda e,s=item: self.valdict.update({s:e})
        if not item in self.fieldlist:
            self.fieldlist.append(item)
        meth(e)
        if self.sendall:
            ext=self.output
        else :
            ext=lambda s=item:self.output(self.valdict.get(s))
        ext()

    def cut(self,e):
        self.clip=e

    def paste(self,field,pos):
        flist= [(i.val,self.valdict[i]) for i in self.fieldlist  if i!=field]
        if self.unique and True in [field.val==f[0] for f in flist]:
            #NB: written like this rather than with 'in' to allow overload of __eq__
            return False
        flist.insert(pos,(field.val,self.valdict[field] ))
        self.clip=None
        self.set_list(flist)
        self.output()


    def input_menu(self,item='None',**kwargs):
        #if hasattr(self.val,'__iter__'):
            #val=self.val[1]
            #key=self.val[0]
        #else:
            #val=self.val
            #key=None
            #self.unselect()
        #print val, key, self.valdict, self.fieldict
        key=None
        if item in self.valdict:
            val=self.valdict[item]
            key=item
            if hasattr(val,'__iter__'):
                key,val=self.val
        else:
            val=None
        opts={}
        opts.update(self.opts)
        meth= lambda e,s=item,k=key:self.changevals(e,s,k)
        opts.setdefault('parent_window',self.parent)
        if not hasattr(self.opts['type'],'__iter__'):
            typ=kwargs.get('type',opts.pop('type'))
        else:
            dtyp=opts.pop('type')
            if val:
                try:
                    typ=val.type
                except:
                    typ=val.__class__
                try:
                    typ=(typ,val.typ)
                except:
                    pass
            else:
                typ=kwargs.get('type',dtyp[0])

        user.ui.input_menu(typ, meth,val=val,on_exit=self.unselect,**opts)

