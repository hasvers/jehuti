from gv_ui_complete import *


class WindowField(UI_Item):
    fixsize=True
    _minsize=None
    _maxsize=None
    status_tip=None #Tip in the status bar
    typecast=None
    mouseover=None #Floating tip

    val=None
    def __init__(self,parent,**kwargs):
        UI_Item.__init__(self,**kwargs)
        self.priority=deepcopy(self.priority)
        pg.sprite.Sprite.__init__(self)
        self.width,self.height=graphic_chart['window_field_std_size']
        self.parent=parent
        for i,j in kwargs.iteritems():
            if i in ('w','wid','width') :
                self.width = j
            if i in ('h','hei','height') :
                self.height = j
            if i=='fixsize':
                self.fixsize=j
            if i=='maxsize':
                self._maxsize=j
            if i=='minsize':
                self._minsize=j
            if i=='val':
                self.val = j
            if i=='typecast':
                self.typecast = j
            if i =='output_method' :
                self.bind_command(j,self.val)
            if i == 'tip':
                self.status_tip=j
            if i=='mouseover':
                self.mouseover=j
        self.image=pg.surface.Surface((self.width,self.height))
        self.image.set_colorkey(COLORKEY)
        self.image.fill(COLORKEY)
        self.rect=self.image.get_rect()

    @property
    def minsize(self):
        if self._minsize:
            return self._minsize
        else:
            return (self.width,self.height)
    @minsize.setter
    def minsize(self,val):
        self._minsize=val

    @property
    def maxsize(self):
        if self._maxsize:
            return self._maxsize
        try:
            return self.parent.field_maxsize()
        except:
            return None


    def set_val(self,val,**kwargs):
        if val!=self.val and not val is None:
            self.val=val
        try:
            self.parent.dirty=1
        except:
            pass

    def output(self,method=None,vals=None ):
        if vals is None :
            try :
                vals=self.val,
            except:
                vals=()
        if self.typecast:
            vals = tuple(self.typecast(v) if v else self.typecast() for v in vals)
        if not method :
            self.parent.exe_command(self,val=vals)
            return True
        if method :
            if hasattr(method,'__iter__'):
                for i in method: self.output(i,vals)
            elif isinstance(method,basestring):
                self.parent.exe_command(self,command =method)
            else :
                self.parent.exe_command(self, command = (method,vals))
            return True
        return False

    def stop_output(self):
        self.parent.rem_from_queue(self)
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

    def unbind_command(self,method=None,delete=False):
        #if delete, remove this field from parent field_commands altogether
        self.parent.rem_command(self,method,delete=delete)


    def resize(self,size):
        if (self.width,self.height)!=tuple(size):
            self.width=self.rect.w=size[0]
            self.height=self.rect.h=size[1]
            self.image=pg.surface.Surface((self.width,self.height),pg.SRCALPHA)
            self.image.set_colorkey(COLORKEY)
            self.image.fill(COLORKEY)
            self.redraw()

    def draw_bg(self,color,rect=None):
        '''Generic function for simple backgrounds.'''
        self.bg=self.image.copy()
        if not rect:
            rect=pg.rect.Rect((0,0),self.rect.size)

        self.bg.fill(COLORKEY)
        if len(color)==2:
            if self.direction == 0 :
                self.bg.blit(gradients.horizontal(rect.size, *color),rect.topleft)
            else :
                self.bg.blit(gradients.vertical(rect.size, *color),rect.topleft)
        else :
            self.bg.fill(color,rect)


    def kill(self,*args):
        self.unbind_command(None,True)
        UI_Item.kill(self,*args)


    def set_state(self,state,*args,**kwargs) :
        if UI_Item.set_state(self,state,*args,**kwargs):
            if state=='hover' and self.mouseover and not self.is_disabled:
                if not user.mouseover or user.mouseover.source!=self:
                    user.set_mouseover(self.mouseover,bg=graphic_chart['mouseover_bg'],
                        anim='appear',len=ANIM_LEN['short'],delay=ANIM_LEN['long'],
                        source=self)
            if state=='hover' and self.status_tip:
                user.set_status(self.status_tip)
            return True
        return False

    def rm_state(self,state,*args,**kwargs) :
        if UI_Item.rm_state(self,state,*args,**kwargs):
            if state=='hover':
                if self.mouseover and user.mouseover and user.mouseover.source==self:
                    user.kill_mouseover()
                if self.status_tip:
                    user.set_status('')
            return True
        return False

class IconField(WindowField):

    state_list=('idle','hover','select','disabled')

    def __init__(self,parent,**kwargs):
        WindowField.__init__(self,parent,**kwargs)
        self.images['idle']=ICONLIB['none']
        self._minsize=self._maxsize=self.images['idle'].get_rect().size
        self.redraw()
        self.set_state('idle')

    def set_val(self,val):
        if val==self.val:
            return
        self.val=val
        self.redraw()

    def redraw(self):
        if not self.val in ICONLIB:
            self.images['idle']=ICONLIB['none']
            for i in ('hover','disabled'):
                if i in self.images:
                    del self.images[i]
        else:
            img=ICONLIB[self.val]
            self.images['idle']=img.copy()
            himg=img.copy()
            gv_effects.glow(himg)
            self.images['hover']=himg
            dimg=img.copy()
            dimg=gv_effects.convert_to_greyscale(dimg, (.5,.5,.5))
            self.images['disabled']=dimg
        try:
            self.parent.dirty=1
        except:
            pass


    def color_mod(self,state,*args):
        if state =='disabled':
            return 'grayed'
        return (1,1,1,1)


    def event(self,event,**kwargs):
        if event.type == pg.MOUSEBUTTONUP:
            if event.button ==1 :
                self.parent.exe_command(self)
                return True
        return False


class TextField(WindowField):
    selectable=False
    focusable=False
    hoverable=True
    highlightable=False #For copy/paste
    basecolor = False
    bgcolor = (0,0,0,0)
    box=False
    maxlines=1
    halign = 'l'
    fixsize=False
    scrollable=False
    hypertext=False
    offset=(0,0)
    padding=(4,2,4,2)
    _font=None

    curval=-1
    linehei=False
    hover_word=None
    interpret=True #interpret code e.g. color, font

    class Word(object):
        sticky=False
        hover,select,highlight=0,0,0
        referent=None
        cache={}
        def __init__(self,**kwargs):
            kws=('txt','rect','color','font','img','referent','sticky')
            for kw,arg in kwargs.iteritems():
                if kw in kws:
                    setattr(self,kw,arg)
        def get_rect(self):
            try:
                return self.rect
            except:
                try:
                    return self.img.get_rect()
                except:
                    return None
        def __str__(self):
            return self.txt

        def render(self,**kwargs):
            font=kwargs.get('font',self.font )
            if 'color' in kwargs:
                color=kwargs['color']
            else:
                try:
                    color=self.color
                except:
                    color=kwargs.get('dft_color')
            if self.select:
                color=[min(255,int(color[i]*graphic_chart['icon_select_color_mod'][i])) for i in range(3)]
                #font.underline(1)
            elif self.hover:
                color=[min(255,int(color[i]*graphic_chart['icon_hover_color_mod'][i])) for i in range(3)]
                #font.underline(1)
            #else:
                #font.underline(0)
            txt=self.txt
            style=kwargs.get("style",font.style() )
            if (txt,font,color,style) in self.cache:
                rend= self.cache[(txt,font,color,style)]
            else:
                if graphic_chart['text_borders']:
                    rend=pgu_writen(txt,font,color)
                else:
                    rend=font.render(txt,1,color)
                ckeys=self.cache.keys()
                if len(ckeys)>database["word_cache_limit"]:
                    del self.cache[ckeys[0]]
                self.cache[(txt,font,color,style)]=rend
                        #TODO render on rect with height given by font.get_linesize()

            if self.highlight:
                cp=rend.copy()
                cp.fill( (225,225,225,100))
                self.img=cp
                self.img.blit(rend,(0,0))
            else:
                self.img=rend
            self.rect=rend.get_rect()

    def __init__(self,parent,**kwargs):
        self.offset=array(self.offset)
        self.highlight_words=[]
        WindowField.__init__(self,parent,**kwargs)
        self.index=-1
        self.state_list+='negative',
        self.priority['negative']=3
        self.box=graphic_chart['text_boxes']
        self.image=pg.surface.Surface((self.width,self.height),pg.SRCALPHA)
        draw=True
        if self.val is None or not unicode(self.val):
            self.val=''
        for i,j in kwargs.iteritems():
            if i=='selectable' :
                self.selectable = j
            elif i in ('hyper','hypertext') :
                self.hypertext = j
            elif i=='bgcolor':
                self.bgcolor=j
            elif i=='color':
                self.basecolor=get_color(j)
            elif i=='box' :
                self.box = j
            elif i=='draw':
                draw =j
            elif i =='wrap':
                if j :
                    self.maxlines = None
            elif i =='maxlines':
                self.maxlines=j
            elif i =='halign':
                self.halign = j
            elif i =='padding':
                if not hasattr(j,'__iter__'):
                    self.padding =(j,j,j,j)
                else :
                    self.padding=  j
            elif i=='font':
                self._font=j
        if draw :
            self.redraw()
            self.rect=self.image.get_rect()

    @property
    def sound(self):
        return  self.selectable or self.focusable

    @property
    def font(self):
        if self._font:
            return  self._font
        return FONTLIB["base"]

    @font.setter
    def font(self,val):
        self._font=val

    def rm_state(self,state,**kwargs):
        if state=='hover' and self.hover_word:
            self.set_word_state(self.hover_word,hover=0,select=0)
        #if state in ('disabled','negative') and not kwargs.get('invisible',0):
            #kwargs['force_remake']=True
        handled= WindowField.rm_state(self,state,**kwargs)
        if handled and state in ('disabled','negative'):
            self.redraw(force_remake=True)
        return handled

    def set_state(self,state,force_redraw=False,**kwargs):
        if state=='hover' and not self.hoverable:
            return False
        if state=='select' and not self.selectable:
            return False
        if state =='focus' and not self.focusable:
            return False
        #if state in ('disabled','negative','idle') and not kwargs.get('invisible',0):
            #kwargs['force_remake']=True
        handled= WindowField.set_state(self,state,force_redraw,**kwargs)
        if handled and state in ('disabled','negative','idle') and not kwargs.get('invisible',0) :
            self.redraw(force_remake=True)
        return handled

    def base_color(self):
        if self.basecolor:
            return self.basecolor
        if self.is_disabled:
            return graphic_chart['text_color_disabled']
        if self.states.get('negative',False):
            return graphic_chart['text_color_negative']
        return graphic_chart['text_color_label']

    def partition(self,txt):
        l=[]
        cur=''
        idx=0
        links=[]
        while txt:
            i=txt[0]
            txt=txt[1:]
            oi=i.replace('"','').replace("'",'')
            ocur=cur.replace('"','').replace("'",'')
            tests=array((oi.isalnum() and ocur.isalnum(),
                cur and cur[0]=="%"  , #and not oi.isspace(),
                links and links[-1][:2]=='%r' and i!='%', #hyperlinks stay grouped
                oi.isspace() and ocur.isspace() ),dtype='bool')
            if tests.any():
                cur+=i
                if cur[0]=='%' ==i:
                    l.append((idx,cur))
                    if cur[1]=='r': #hyperlink detection
                        links.append(cur)
                    elif links:
                        links.pop()
                    cur=''
            else :
                if cur:
                    l.append( (idx,cur))
                cur=i
            idx+=1
        l.append((idx,cur))
        return l

    def make_table(self,txt=None,**kwargs):
        if  txt==None:
            txt=self.val
        try:
            if txt==self.curval and not kwargs.get('force_remake',False):
                return
        except:
            pass
        self.curval=txt
        self.content=[]
        self.lines=[]
        if not txt:
            return
        parag=txt.splitlines()
        if self.maxlines and len(parag)>self.maxlines: #too many lines, put all the surnumerary in the last one
            supp=parag[self.maxlines:]
            parag=parag[:self.maxlines]
            for s in supp:
                parag[-1]+=s
        options=[{'color':self.base_color(),'font':self.font,'referent':None,
            'b':0,'i':0,'u':0} ]
        font=self.font
        for p in parag:
            self.content.append([])
            l=self.partition(p)
            if not l:
                continue
            for idx, w in l: #Right now i dont use idx at all, should I remove it?
                if not w:
                    continue
                if self.interpret and len(w)>1 and w[0]== w[-1]=='%': #options
                    if w[1]=="%":
                        if len(options)>1: #remove the last option
                            options.pop(-1)
                    else:
                        newopt={}
                        newopt.update(options[-1])
                        if w[1]=='c':
                            newopt['color']=get_color(w[2:-1])
                        if w[1]=='f':
                            newopt['font']=w[2:]
                        if w[1]=='r':
                            newopt['referent']=w[2:-1]
                        if w[1] in ('b','i','u'):
                            newopt[w[1]]=1
                        options.append(newopt)
                    font =options[-1]['font']
                    for tx,fun in (('b',font.strong),('i',font.oblique),
                        ('u',font.underline)):
                        if options[-1][tx]:
                            fun(1)
                        else:
                            fun(0)
                else:

                    if  w.isalnum() or not w.isspace() :
                        sticky=False
                        if not unicode(w).translate({ch:'' for ch in ',;:!?.'}):
                            sticky='l'
                            if w=='.':
                                sticky='lr'

                        w=self.Word(txt=w,sticky=sticky,**options[-1])
                    else:
                        w=self.Word(txt=w,font=font)
                    w.render(dft_color=self.base_color() )
                    toappend=None
                    try:
                        ls= self.content[-1][-1][-1].sticky
                        if not ls:
                            ls=''
                        if unicode(w.txt).isspace() or not (( 'r' in ls )or ('l' in w.sticky)):
                            self.content[-1].append([])
                        else:
                            toappend=self.content[-1][-1]
                    except:
                        self.content[-1].append([])
                    if not toappend:
                        toappend=self.content[-1][-1]
                    toappend.append(w)

        #print self.content
        self.upd_table()

    def upd_table(self,line=None):
        curpos=array((0,0))
        dbpad= array(self.padding[:2])+array(self.padding[2:])
        if line!=None and line < len(self.lines):
            if line <len(self.lines)-1:
                nextline=self.lines[line+1]
            else:
                nextline=None
            for ic,c in enumerate(self.lines[line]):
                rect=c.get_rect()
                rect.topleft=curpos
                if curpos[0]+array(rect.w) > self.width - dbpad[0]:
                    #line too long now
                    return self.upd_table()

                if nextline:
                    if curpos[0]+array(rect.w)+nextline[0].get_rect().w < self.width - dbpad[0]:
                        #line too short now
                        return self.upd_table()
            return

        self.lines=[[]]
        self.linelen=[0] #length in terms of index
        self.linehei=[]
        self.linewid=[0]
        for p in self.content: #paragraphs
            height=self.font.get_linesize()
            for clist in p:
                #c is a list including sticky words
                #if not hasattr(clist,'__iter__'):
                    #clist=[clist]
                rw=0
                for c in clist:
                    rect=c.get_rect()
                    rect.topleft=curpos
                    if rect.h>height:
                        height=rect.h
                    curpos[0]+=rect.w
                    rw+=rect.w
                if curpos[0] > self.width - dbpad[0]:
                    v1=(self.fixsize and self.fixsize!= 'v')
                    v2=(self.maxsize and  curpos[0]+ dbpad[0] > self.maxsize[0] )
                    if v1 or v2:
                        if not self.maxlines or len(self.lines)<self.maxlines:
                            self.lines.append([])
                            self.linewid.append(0)
                            self.linelen.append(0)
                            curpos[0]=rw
                            curpos[1]+=height
                            self.linehei.append(height)
                    else:
                        self.width = curpos[0]+ dbpad[0]

                for c in clist:
                    self.lines[-1].append(c)
                    self.linelen[-1]+=len(c.txt)
                    self.linewid[-1]+=c.get_rect().w
            if p!= self.content[-1]:
                self.lines.append([])
                self.linewid.append(0)
                self.linelen.append(0)
                curpos[0]=0
                curpos[1]+=height
                self.linehei.append(height)
                height=0

        self.linehei.append(height)
        if  not self.fixsize or self.fixsize=='h' :
            self.height=sum(self.linehei)+dbpad[1]
        return

    def write(self,txt=None,bgcolor=None,image=None,**kwargs):
        txtcolor=kwargs.get('color',self.base_color())
        if txt is None:
            txt=self.val
        if not txt is None:
            txt=unicode(txt)
        #print txt,self.offset, debug.caller_name(),
        #try:
            #print self.index
        #except:
            #print ''
        if not bgcolor:
            bgcolor=self.bgcolor
        if self.curval!=txt or kwargs.get('force_remake',False):
            self.make_table(txt,**kwargs)
        if not image:
            image=pg.surface.Surface((self.width,self.height),pg.SRCALPHA)
        if txt is None or not txt:
            image.fill(bgcolor)
            if kwargs.get('return_bb',False):
                return image,(self.width,self.height)
            return image
        pad=array(self.padding[:2]+(0,0))
        pad[:2]+=self.offset
        pos=array( (0,0))
        idx=0
        if self.fixsize:
            maxwid=self.width- sum(self.padding[0::2])
        else:
            maxwid=max(self.linewid)
        for idl,l in  enumerate(self.lines):
            pos[0]=0
            if self.halign=='c':
                pos[0]=(maxwid-self.linewid[idl])/2
            elif self.halign=='r':
                pos[0]=maxwid-self.linewid[idl]

            for c in l:
                if hasattr(c,'img'):
                    if 'color' in kwargs:
                        c.render(color=txtcolor)
                    else:
                        c.render(dft_color=txtcolor)
                    img=c.img
                else:
                    img=c
                image.blit(img,pos+pad[:2] )
                if self.is_focused  and idx<=self.index and idx+len(c.txt)> self.index :
                    #print c.txt,idx,self.index
                    dpos=array(c.font.size( c.txt[:self.index-idx]))
                    dpos[1]=0
                    image.blit(c.font.render(self.focus_mark,1,txtcolor),
                        pos+pad[:2]+dpos )
                c.rect.topleft=pos+pad[:2]
                pos[0]+=c.get_rect().w
                idx+=len(c.txt)
            #if len(heis)>1:
                #pos[1]+=heis.pop(0)
            if idl<len(self.lines)-1:
                pos[1]+=self.linehei[idl]
            else:
                pass
        if self.is_focused  and idx<=self.index:
            image.blit(c.font.render(self.focus_mark,1,txtcolor),pos+pad[:2] )
        bb= (max(self.linewid),sum(self.linehei))
        img=pg.surface.Surface((self.width,self.height),pg.SRCALPHA)
        img.fill(bgcolor)

        img.blit(image,(0,0))
        if kwargs.get('glow',0):
            gv_effects.glow(img)
        if kwargs.get('return_bb',False):
            return img,bb
        return img



    def change_word(self):
        #if needed I will make a clever dynamical parser
        #that checks whether it needs to extend a word, break it down
        #and so on depending on input and then updates only the proper line
        self.upd_table(line)
        pass

    def redraw(self,txt=None,**kwargs):
        if txt ==None :
            txt = self.val
        else :
            self.val=txt
        bounding_box=(0,0)
        if self.selectable or self.focusable :
            self.images ={}
            txtcolors,bgcolors={},{}
            if self.selectable :
                states = ('idle','hover','select','disabled')
                txtcolors = {s:graphic_chart['text_color_'+s] for s in states}
                colors = txtcolors
            elif self.focusable :
                states = ('idle','hover','focus','disabled')
                bgcolors = {s:graphic_chart['window_field_bg_'+s] for s in states}
                colors = bgcolors
            if 0 and self.box and self.hoverable and not array(self.bgcolor).any():
                bgcolors['hover']=graphic_chart['window_field_text_hover']
            for i in states:
                kw={}
                kw.update(kwargs)
                bgcolor=bgcolors.get(i,None)
                if i in txtcolors:
                    kw['color']=txtcolors[i]
                if i=='hover':
                    kw['glow']=1
                self.images[i],bb=self.write(txt,bgcolor,return_bb=True,**kw)
                bounding_box=npmaximum(bounding_box,bb)
                if self.box and self.selectable :
                    img=self.images[i]
                    if i == 'select' :
                        pg.draw.rect(img,(130,130,150,255),img.get_rect(),3)

            self.image=self.images.get(self.state,self.images['idle'])
        else :
            self.image,bounding_box=self.write(txt,return_bb=True,**kwargs)
        if not self.fixsize and self.linehei:
            dbpad=array(self.padding[:2])+self.padding[2:]
            self.minsize=tuple(dbpad+bounding_box)
        try:
            self.parent.dirty=1
        except:
            pass

    def event(self,event,*args,**kwargs):
        if self.is_disabled:
            return False
        if self.selectable:
            if event.type == pg.MOUSEBUTTONUP and event.button==1 :
                self.parent.select(self)
                if self.is_selected:
                    return self.output(None,())
                else :
                    return self.stop_output()
            #else :
                #return False

        if self.hoverable and (self.hypertext or event.type == pg.MOUSEBUTTONDOWN or pg.mouse.get_pressed()[0]):
            if event.type in (pg.MOUSEMOTION,pg.MOUSEBUTTONDOWN) :
                refpos=array(self.parent.abspos(self))
                for i,j in kwargs.iteritems():
                    if i=='refpos':
                        refpos=array(j)
                pos = tuple( array(event.pos)-refpos )
                #if 1 or self.rect.collidepoint(pos):
                idx,widx=self.locate(pos,1)
                if  event.type==pg.MOUSEBUTTONDOWN and event.button==1:
                    if self.hypertext and widx and widx.referent:
                        reft=eval(widx.referent)
                        event=Event(*reft[1],type='hyperlink',source='hyperlink',**reft[2])
                        user.evt.pass_event(event,self,True)
                        self.set_word_state(widx,hover=1,select=1)
                        return True

                    self.remove_highlights()
                elif self.hypertext and widx and widx.referent:
                    if not widx.hover:
                        self.set_word_state(widx,hover=1)
                else :
                    self.set_word_state(self.hover_word,hover=0,select=0)
                if not self.selectable and self.highlightable and event.type ==pg.MOUSEMOTION and pg.mouse.get_pressed()[0]:
                    self.set_word_state(widx,highlight= 1)


        return False

    def set_word_state(self,word,**kwargs):
        if not word:
            return
        for i,j in kwargs.iteritems():
            if i=='hover':
                if j:
                    if self.hover_word!=word:
                        self.set_word_state(self.hover_word,hover=0,select=0)
                    self.hover_word=word
                    user.set_status('Hyperlink: '+eval(word.referent)[0])
                elif self.hover_word==word :
                    self.hover_word = None
                    user.set_status('')
            if i=='highlight' :
                if j and not word.highlight:
                    self.highlight_words.append(word)
                    txt=''.join([z.txt for z in self.highlight_words ])
                    clipboard.copy(txt)
                if not j:
                    try:
                        self.highlight_words.remove(word)
                    except:
                        pass
            if hasattr(word,i):
                setattr(word,i,j)
        word.render()
        self.redraw()

    def remove_highlights(self):
        if not self.highlight_words:
            return
        for w in self.highlight_words:
            w.highlight=0
            w.render()
        self.highlight_words=[]
        self.redraw()

    def set_val(self,val,redraw=True):
        if val!=self.val:
            WindowField.set_val(self,val)
            self.val=val
            if redraw:
                self.redraw()
            return True
        return False

    def locate(self,pos,word=0):
        #given coordinates, find where they fall into the text in terms of index
        idx=0
        sumhei=0
        widx=None
        for il,l in enumerate(self.lines):
            if widx:
                break
            sumhei+=self.linehei[il]
            if pos[1]> sumhei:

                idx+=self.linelen[il]
                continue
            for c in l:
                if c.rect.collidepoint(pos):
                    sup=0
                    while c.rect[0]+2+c.font.size(c.txt[:sup+1])[0]<pos[0]:
                        sup+=1
                    idx+=sup
                    widx=c
                    break
                idx+=len(c.txt)
        if not word:
            return idx
        else :
            return idx,widx
