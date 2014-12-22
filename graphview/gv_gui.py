# -*- coding: utf-8 -*-
from gv_gui_windows import *
import os
from gv_audio import *



class BasicUI(UI_Widget):
    name='basicUI'
    def __init__(self,screen,**kwargs):
        self.bg=kwargs.pop('bg',None)
        template=kwargs.pop('template',ergonomy)
        if not hasattr(self,'soundmaster'):
            self.soundmaster = kwargs.pop('soundmaster',BasicSM(self))
        self._screen=screen
        self.store={} #store default interface parameters to return to
        self.view={}
        self.window={}
        self.wintypes=kwargs.pop('wintypes',{} ) #constructors for default window types e.g.panels
        self.stackable=template.get('stackables',[])
        self.wseq=[] #sequential order of viewables from top to bottom

        self.layers=[]#order in which widgets other than windows must be called and painted
        self.veils={}#for fade, pause etc.
        self.balloons={} #for balloons: anything that attaches a window to a ui item
        UI_Widget.__init__(self)

        self.depend=DependencyGraph()

        self.group=pgsprite.LayeredUpdates()
        self.floatgroup=pgsprite.LayeredUpdates()
        self.rect=self.screen.get_rect()
        self.available=self.rect.move(0,0)
        self.visual_queue=[] #queue for visual effects
        self.anim=AnimationHandler() #Replacement for visual_queue

        for i in template['viewables']: #all possible viewables for any kind of UI
            self.store[i]=template[i]
            self.view[i]=template[i]
            self.window[i]=None
            self.wseq.append(i)
            if self.view[i] and i in self.wintypes:
                self.show(i)

    def launch(self):
        #Things that should happen after the UI has been set as user.ui
        #e.g. anything that may involve passing events

        self.stack=user.evt.stack
        self.undo_stack=user.evt.undo_stack
        self.make_dependencies()

    def make_dependencies(self):
        self.depend.clear()
        self.depend.add_dep(self.soundmaster,user)
        for i,window in self.window.iteritems():
            if window:
                try:
                    window.make_dependencies()
                except:
                    pass

    @property
    def screen(self):
        if self._screen:
            return self._screen
        else:
            return user.screen

    @property
    def components(self):
        return ()


    def kill(self):
        self.group.empty()
        self.floatgroup.empty()
        self.view={}
        for i,j in self.window.iteritems():
            if hasattr(j,'__iter__'):
                [k.kill() for k in j]
            elif j :
                j.kill()
        self.window={}
        for l in self.layers :
            try :
                l.group.empty()
            except :
                pass
        self.layers=[]

        super(BasicUI,self).kill()

    def float_menu(self,struct,**kwargs):
        kwargs.setdefault('ephemeral',False)
        kwargs.setdefault('oneshot',True)
        window=FloatMenu(self.screen,self,graphic_chart['float_base_size'],
            struct=struct,**kwargs)
        window.set_command('exit',lambda : self.close(window))
        window.set_anim('appear',len=ANIM_LEN['instant'])
        for c in window.children:
            c.set_anim('appear',len=ANIM_LEN['short'])
        return  self.float_core(window,'floatmenu',**kwargs)

    def float_core(self,window,typ='floatmenu',**kwargs):
        if 'parent_window' in kwargs:
            kwargs['parent_window'].children.append(window)
        bbox=kwargs.get('bbox',self.screen.get_rect())
        if typ=='balloon':
            window.set_command('exit',lambda : self.close_balloon(window))
        else:
            window.set_command('exit',lambda : self.close(window))
        window.update()
        pos=kwargs.get('pos',None)
        if  pos is None:
            pos=user.mouse_pos()-array((16,16))
        elif pos is 'center':
            pos=array(self.rect.center)-window.rect.center
        window.rect.topleft=pos
        window.rect.clamp_ip(bbox)
        self.pos[window]=window.rect.topleft
        #print self.stackable
        if not typ in self.stackable or not self.stackable[typ]:
            self.close(self.window[typ])
            self.window[typ]=window
        else:
            if not self.window[typ]:
                self.window[typ]=[]
            if 'reverse' == self.stackable[typ]:
                [self.floatgroup.remove(w) for w in self.window[typ]]
                self.window[typ].insert(0,window)
                [self.floatgroup.add(w) for w in self.window[typ]]
            else:
                self.window[typ].append(window)
        if not window in self.floatgroup:
            self.floatgroup.add(window)
        return  window

    def make_balloon(self,txt,**kwargs):
        pointpos=kwargs.pop('pos',None)
        anchor=kwargs.pop('anchor','')
        if anchor and not isinstance(anchor,basestring) and pointpos is None:
            try:
                pointpos=anchor.get_hotspot(balloon=True)
            except:
                pointpos=anchor.rect.topleft

        w,h=graphic_chart['dialbox_size']
        rect=self.screen.get_rect()
        ball=SpeechBalloon(self,(w,h),maxsize=array(self.rect.size)*.5,fixsize=0,**kwargs)
        ball.add('text',val=txt,wrap=True,maxlines=None,font=fonts["dialogue"])
        brect=ball.rect
        w,h=brect.size
        bs=self.balloons.setdefault(anchor,[])
        if  not anchor:
            brect.center=rect.center
            pos=brect.topleft
        elif isinstance(anchor,basestring):
            anchor=anchor.lower()
            if anchor=='up':
                brect.center=(rect.center+3*array(rect.midtop))/4
            elif anchor=='down':
                brect.center=(rect.center+3*array(rect.midbottom))/4
            else:
                brect.center=rect.center
            pos=brect.topleft

        else:
            dist=(rect.center+2*array(rect.midtop))/3 -pointpos

            if dist[1]<=0:
                drct='b'
            else:
                drct='t'
            if dist[0]<=0:
                drct+='r'
            else:
                drct+='l'

            bpos=(60,0,0,30)
            pos = pointpos+array((0,-h))

            if drct=='bl':
                bpos=(60,0,0,30)
            if drct=='br':
                bpos=(0,0,-60,30)
            if drct=='tl':
                bpos=(60,-30,0,0)
            if drct=='tr':
                bpos=(0,-30,-60,0)
            if 'r' in drct:
                pos-=array((w,0))
            if 't' in drct:
                pos+=array((0,h) )


            if not bs:
                ball.set_point(bpos)
            else:
                if kwargs.get('multi',0):
                    #allowing multiple balloons
                    for b in bs:
                        pos += array((0,b.rect.h))
                    ball.set_point(bpos)
                else:
                    for b in bs:
                        if b!=ball:
                            b.closing_event()
                    ball.set_point(bpos)
        bs.append(ball)
        ball.anchor=anchor

        ball.set_anim('appear',len=ANIM_LEN['med'],affects=[ball])
        border=self.screen.get_rect().inflate(w,h)

        self.float_core(ball,'balloon',pos=pos,bbox=border,**kwargs)
        #ballpos=

    def close_balloon(self,ball):
        try:
            self.balloons[ball.anchor].remove(ball)
        except:
            pass
        self.close(ball)

    def trigger_view(self,widget):
        if self.view[widget]:
            self.store[widget]=self.view[widget]
            self.view[widget]=False
            self.hide(widget)

        else :
            if self.store[widget]:
                self.view[widget]=self.store[widget]
            else :
                self.store[widget]=ergonomy[widget]
                self.view[widget]=True
            if self.view[widget]:
                self.show(widget)

    def create_window(self,i):
        wintypes=self.wintypes
        j = wintypes[i](self)
        self.window[i]=j
        if 'panel' in i and i!='sidepanel':
            self.view[i]=self.view['sidepanel']
            self.store[i]=self.store['sidepanel']
        view = self.store[i]
        if view == 'u' :
            j.rect.topleft=self.available.topleft
            dif = (0,j.rect.h/2 )
        elif view =='d' :
            j.rect.bottomleft=self.available.bottomleft
            dif = (0,-j.rect.h/2 )
        elif view =='r':
            j.rect.topright=self.available.topright
            dif = (-j.rect.w/2 ,0)
        elif view =='l':
            j.rect.topleft=self.available.topleft
            dif = (j.rect.w/2 ,0)
        if not 'panel' in i:
            self.available.inflate_ip(-2*abs(dif[0]),-2*abs(dif[1]))
            self.available.move_ip(*dif)
        self.pos[j]=j.rect.topleft

    def hide(self,window):
        #kills window but not its children
        if window in self.window:
            w= self.window[window]
            if hasattr(w,'__iter__'):
                [k.kill(recursive=False) for k in w]
            elif w:
                w.kill(recursive=False)
            if 'panel' in window:
                i='sidepanel'
            else:
                i=window
            self.view[i]=False
            return True
        else :
            return False

    def show(self,window):
        if not window in self.window or not self.window[window]:
            self.create_window(window)
        w= self.window[window]
        if 'float' in window:
            group= self.floatgroup
        else:
            group=self.group
        if hasattr(w,'__iter__'):
            [group.add(k) for k in w]
        elif w:
            group.add(w)
        if 'panel' in window:
            i='sidepanel'
        else:
            i=window
        if hasattr(w,'refresh'):
            w.refresh()
        self.view[i]=self.store[i]

    def update(self):
        for l in self.layers:
            l.update()

    def confirm_menu(self,output_method,**kwargs):
        window=FloatMenu(self.screen,self,(128,100),oneshot=True,**kwargs)
        window.add('text',val=kwargs.pop('legend','Are you sure?'),selectable=False,colspan=2)
        window.add('text',val='Ok',output_method=output_method,selectable=True,pos=(1,0))
        window.add('text',val='Cancel',output_method='exit',selectable=True,pos=(1,1))
        self.float_core(window,'floatmenu',**kwargs)

    def save_menu(self,typ,output_method,**kwargs):
        default=''
        for i, j in kwargs.iteritems():
            if i =='default' :
                default =j
        if 'path' in kwargs:
            path=kwargs['path']
        else:
            path=database[typ+'_path']
        candidates = olistdir(path)
        print path,candidates
        flist=[]
        window=FloatMenu(self.screen,self,(128,100),oneshot=True,**kwargs)
        v=0
        ext=kwargs.get('ext',database.get(typ+'_ext',''))
        for c in candidates:
            if ext in str(c):
                flist.append((str(c),str(c).replace(ext,'') ))
        if flist :
            window.add('text',val='Overwrite:',selectable=False,pos=(0,0) )
            v+=1
            window.add('list',val=flist,output_method=output_method,pos=(v,0))
            v+=1
        window.add('text',val='New file:',selectable=False,pos=(v,0) )
        v+=1
        tmp=window.add('input',val=default,width=150,pos=(v,0),allchars='alnum')
        tmp.bind_command(output_method,default)
        window.add('text',val=kwargs.get('ext',database.get(typ+'_ext','')),selectable=False,pos=(v,1))
        v+=1
        window.add('text',val='Ok',output_method='confirm',selectable=True,pos=(v,0))
        window.add('text',val='Cancel',output_method='cancel',selectable=True,pos=(v,1))
        self.float_core(window,'floatmenu',**kwargs)

    def load_menu(self,typ_or_list,output_method,**kwargs):
        if hasattr(typ_or_list,'__iter__'):
            if 'path' in kwargs:
                path=kwargs['path']
                flist= [(str(c),path+str(c)) for c in typ_or_list ]
            else:
                flist=typ_or_list
        else:
            typ=typ_or_list
            path=kwargs.get('path',database[typ+'_path'])
            candidates = olistdir(path)
            flist=[]
            for c in candidates:
                if kwargs.get('ext',database.get(typ+'_ext','')) in str(c):
                    flist.append((str(c),path+str(c)))
        window=FloatMenu(self.screen,self,(128,100),oneshot=True,**kwargs)
        window.ask_confirm()
        window.add('text',val='Files:',selectable=False)
        if flist :
            window.add('list',val=flist,output_method=output_method)
        else :
            window.add('list',val=[('No file found','')],selectable=False)
        cont = FieldContainer(window,margin=8,maxsize=self.screen.get_rect().size)
        cont.add('okbutton',val='Ok',selectable=True,pos=(0,0),width=50)
        cont.add('text',val='Cancel',output_method='cancel',selectable=True,pos=(0,1),width=50)


        if kwargs.get('new',None) :
            cont.add('text',val='New',output_method=(kwargs['new'],'confirm'),selectable=True,pos=(0,0),width=50)
        cont.update()
        #print cont.size, cont.minsize, cont.maxsize, cont.rect.size
        window.add(cont,pos=(2,0))
        self.float_core(window,'floatmenu',**kwargs)

    def input_menu(self,typ,output_method,**kwargs):
        window=FloatMenu(self.screen,self,(128,10),oneshot=True,**kwargs)
        window.draggable=True
        for i,j in kwargs.iteritems():
            if i =='on_exit':
                window.set_command('exit',j)
        window.ask_confirm()
        window.add('text',val=kwargs.pop('title','Value:'),selectable=False)
        tmp=window.add(typ,**kwargs)
        tmp.bind_command(output_method,**kwargs)
        cont = FieldContainer(window,margin=8,maxsize=self.screen.get_rect().size)
        cont.add('text',val='Ok',output_method='confirm',selectable=True,pos=(0,0),width=50)
        cont.add('text',val='Cancel',output_method='cancel',selectable=True,pos=(0,1),width=50)
        cont.update()
        window.add(cont)
        tmp.output()
        self.float_core(window,'floatmenu',**kwargs)

    def close(self,window) :
        if window in self.window:
            w= self.window[window]
            self.window[window]=None
            if hasattr(w,'__iter__'):
                [k.kill() for k in w]
            elif w:
                w.kill()
            return
        if not window:
            return
        for i, j in self.window.iteritems() :
            if hasattr(j,'__iter__') and window in j:
                j.remove(window)
                window.kill()
            elif j == window  and j:
                self.window[i] = None
                j.kill()

    def abspos(self,child=None,**kwargs):
        return UI_Widget.abspos(self,child,**kwargs)

    def paint(self,**kwargs):
        if not self.bg:
            self.screen.fill((0,0,0))
        else:
            self.screen.blit(self.bg,(0,0))
        if self.layers :
            exclude = kwargs.pop('exclude',[])
            if not hasattr(exclude,'__iter__'):
                exclude=[exclude]

            lay = self.layers[::-1]
            for l in lay :
                if not l in exclude :
                    if hasattr(l.view,'paint'):
                        l.view.paint(self.screen)
#                        l.group.update()
#                        l.group.draw(self.screen)
                    #except :
                        #pass
        self.group.update()
        self.group.draw(self.screen)

        if user.paused:
            veil=pg.surface.Surface(self.screen.get_rect().size)
            veil.fill( graphic_chart['paused_veil'] )
            veil.set_alpha(graphic_chart['paused_veil'][3])
            self.veils['pause']=veil
        elif 'pause' in self.veils:
            del self.veils['pause']

        for j,veil in self.veils.iteritems():
            self.screen.blit(veil,(0,0))
        self.floatgroup.update()
        self.floatgroup.draw(self.screen)

    def react(self,evt):
        if 'hover' in evt.type :
            user.set_status( evt.kwargs.get('label',None) )

    def event(self,event,**kwargs):
        self.visual_advance()
        exclude = kwargs.pop('exclude',[])
        if not hasattr(exclude,'__iter__'):
            exclude=[exclude]
        if event.type == 31 : # for double clicks
            user.just_clicked=None
            pg.time.set_timer(31,0) # deactivate the just_clicked killer
        if event.type in (pg.MOUSEBUTTONUP, pg.MOUSEMOTION, pg.MOUSEBUTTONDOWN):

            if user.grabbed and user.grabbed.event(event):
                return True

            windowseq= []
            for i in kwargs.pop('wseq',self.wseq):
                if i in self.view and ( not i in exclude ) and self.view[i] and self.window[i]:
                    w=self.window[i]
                    if hasattr(w,'__iter__'):
                        windowseq+=w[::-1]
                    elif w:
                        windowseq.append(w)

            hovering=False
            for w in windowseq:
                if w.rect.collidepoint(event.pos):
                    hovering=True
                    self.hover(w)
                    tmp= w.event(event)
                    if tmp or not w.clickthrough:
                        return tmp
            if not hovering :
                self.unhover()
            if event.type!=pg.MOUSEMOTION and user.focused_on and user.focused_on!=hovering:
                tmp=  user.focused_on.event(event)
                if tmp:
                    return tmp
                user.unfocus()

        if event.type==pg.KEYDOWN :
            if user.focused_on and  user.focused_on.event(event) :
                try:
                    user.focused_on.parent.dirty=1
                except:
                    pass
                return True
            elif self.balloons and event.key in (pg.K_SPACE, pg.K_RETURN):
                for b in tuple(self.balloons):
                    if not self.balloons[b]:
                        del self.balloons[b]
                        continue
                    if self.balloons[b][0].event(event):
                       return True
        if event.type == pg.KEYUP:
            if self.keymap(event):
                return True

        if not user.paused and event.type==30 or not self.window.get('floatdialog',False):
            for l in self.layers :
                if ( not l in exclude ) and l.event(event):
                    return True



        if event.type == pg.MOUSEBUTTONDOWN:
            if 'floatmenu' in self.window and self.window['floatmenu'] :
                self.window['floatmenu'].kill()
                self.window['floatmenu']=None
                return True
            if event.button==3:
                self.general_menu(event)

        return False

    def general_menu(self,event=None):
        struct=()
        if self.stack:
            text=self.stack[-1].desc
            struct+=('Undo '+text,lambda e=None: user.evt.undo(e)  ),
        if self.undo_stack:
            text=self.undo_stack[-1].desc
            struct+=('Redo '+text,lambda e=None: user.evt.redo(e) ),
        for l in self.layers :
            struct+=tuple(l.menu(event))
        if struct:
            self.float_menu(struct)


    def keymap(self,event):
        if array(tuple(pg.key.get_pressed()[i] for i in (pg.K_RCTRL,pg.K_LCTRL) )).any():
            if event.key == pg.K_z:
                print 'undo'
                return user.evt.undo()
            if event.key == pg.K_y:
                return user.evt.redo()
            if event.key==pg.K_p:
                return user.screenshot()
            if pg.key.get_pressed()[pg.K_LALT] and event.key==pg.K_v and database['edit_mode']:
                return user.trigger_video()
            if event.key==pg.K_d and database['edit_mode'] :
                user.debug_mode=1-user.debug_mode
                print 'Debug:', user.debug_mode
                return True

    def add_visual(self,vis):
        self.visual_queue.append(vis)

    def visual_advance(self):
        if not user.evt.moving:
            self.anim.update()
            while self.visual_queue:
                self.visual_queue.pop(0)()

    def set_mouseover(self,txt,anim=None,**kwargs):
        if user.mouseover:
            user.mouseover.kill()
        user.mouseover=Emote(txt,**kwargs)
        if anim:
            user.mouseover.set_anim(anim,**kwargs)
        else:
            user.mouseover.set_anim('appear',len=ANIM_LEN['instant'])
        self.group.add(user.mouseover)
        pos=kwargs.get('pos',None)
        if pos is None:
            pos=user.mouse_pos()
        user.mouseover.rect.bottomleft=pos

    def kill_mouseover(self):
        if user.mouseover:
            user.mouseover.set_anim('disappear',
                len=ANIM_LEN['short'],affects=[user])


class BasicSM(SoundMaster):
    def react(self,evt):
        sgn=evt.type
        if 'loading' in sgn and evt.state==1:
            self.play('load')
        elif 'sound' in evt.kwargs :
            self.play(evt.kwargs['sound'])
        elif 'return' in sgn:
            user.music.stop()
        return True

class EditorUI(BasicUI):
    name='editorUI'
    CanvasEditor=CanvasEditor
    def __init__(self,screen,editable=None,**kwargs):

        if self.statusmenu():
            smenu=[('Menu',self.statusmenu )]
        else:
            smenu=False
        wintypes=kwargs.pop('wintypes',dict((  ('statusbar',lambda e: StatusBar(e,menu=smenu)),
                        ('nodelist',NodeList),
                    )))
        sidetypes=kwargs.pop('sidetypes',('nodepanel','linkpanel'))

        if isinstance(editable,Canvas):
            canvas= editable
            self.canvas=canvas
            wintypes.update(dict(
                        (('sidepanel',lambda e,t=canvas:SidePanel(e,t)),
                        ('nodepanel',lambda e,t=canvas: NodePanel(e,t)),
                        ('linkpanel',lambda e,t=canvas: LinkPanel(e,t)))))
        kwargs['wintypes']=wintypes

        super(EditorUI, self).__init__(screen,**kwargs)

        if isinstance(editable,Canvas):
            if not canvas.handler :
                canvas.set_handler(self.CanvasEditor(canvas,self,self.screen.get_rect().size))
            self.layers.append(canvas.handler)

        else :
            if editable:
                self.layers.append(editable)
        self.hide('sidepanel')

    def temp(self,*params):
        return None

    def statusmenu(self):
        return False

    def make_dependencies(self):
        BasicUI.make_dependencies(self)
        self.canvas.handler.make_dependencies()
        deplist=( (self,self.canvas.handler), )
        if self.window['statusbar']:
           deplist+=(self.window['statusbar'],user),
        [self.depend.add_dep(*d) for d in deplist]

    @property
    def components(self):
        return (self.canvas.handler,)

    def react(self,evt):
        sgn=evt.type
        sarg=evt.args
        if 'edit' in sgn or (ergonomy['edit_on_select'] and 'select' in sgn):
            try:
                item=sarg[0]
            except:
                return False
            if hasattr(item,'item'):
                item=item.item
            try:
                panel=item.type+'panel'
            except:
                panel=item.datatype+'panel'
            self.hide('sidepanel')
            self.show(panel)
            window=self.window[panel]
            self.window['sidepanel']=window
            window.set_ref(item)
            self.show('sidepanel')
        if (ergonomy['edit_on_select'] and 'unselect' in sgn):
            self.hide('sidepanel')
        return  super(EditorUI,self).react(evt)

    def keymap(self,event):
        return BasicUI.keymap(self,event)

    def maker_menu(self,flist,output_method,klass,**kwargs):
        eff=kwargs.pop('val',False)
        if not isinstance(eff,klass):
            eff=klass()
        if 'typecast' in kwargs:
            outme=lambda e,t=kwargs['typecast']: output_method(t(e) )
        else:
            outme=output_method
        flist=EditorMenu.list_format(flist)

        kwargs.setdefault('itemwrite',True)
        kwargs.setdefault('attr',flist)
        kwargs.setdefault('askconfirm',True)
        window=EditorMenu(self,kwargs.pop('data',None),
            ref=eff, **kwargs)

        window.set_command(window.ok_field,(outme,(eff,)) )
        if 'parent_window' in kwargs:
            parent=kwargs['parent_window']
            if hasattr(parent,'ref'):
                updparent=lambda e: e.set_ref(e.ref)
                window.set_command(window.ok_field,(updparent,(parent,)) )
                #window.set_command(window.ok_field,(parent.refresh_fields,() ) )
        window.draggable=True
        self.float_core(window,'stackmenu',**kwargs)

    def input_menu(self,typ,output_method,**kwargs):
        if typ=='xy':
            return self.coord_maker(output_method,**kwargs)
        elif typ=='color':
            return self.color_maker(output_method,**kwargs)
        else :
            return super(EditorUI,self).input_menu(typ,output_method,**kwargs)

    def coord_maker(self,output_method,**kwargs):
        class ArrayMaker(object):
            def __init__(self,ref=None,typ=int):
                self.typ=typ
                if ref is None:
                    self.w,self.h=0,0
                else:
                    self.w,self.h=ref
                self.dft={'w':self.w,'h':self.h}

            def __getitem__(self,i):
                if i:
                    return self.typ(self.h)
                else:
                    return self.typ(self.w)
            def __len__(self):
                return 2
        klass=ArrayMaker
        ref=kwargs.pop('val',None)
        if not isinstance(ref,klass):
            ref=klass(ref)
        legs=kwargs.pop('xylegend','xy')
        kwargs.setdefault('ephemeral',True)
        flist=(
            ('w','input',{'legend':legs[0],'width':200,'allchars':'num','charlist': () }),
            ('h','input',{'legend':legs[1],'width':200,'allchars':'num','charlist':() }),
            )
        kwargs.setdefault('title','Size:')
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)


    def color_maker(self,output_method,**kwargs):
        class ArrayMaker(object):
            def __init__(self,ref=None,typ=int):
                self.typ=typ
                if ref is None:
                    color=0,0,0,0
                else:
                    color=ref
                self.dft={'color'+str(i):color[i] for i in range(4)}
                for i,j in self.dft.iteritems():
                    setattr(self,i,j)

            def __getitem__(self,i):
                return self.typ(getattr(self,'color'+str(i)))

            def __len__(self):
                return 4
        klass=ArrayMaker
        ref=kwargs.pop('val',None)
        if not isinstance(ref,klass):
            ref=klass(ref)
        kwargs.setdefault('ephemeral',True)
        flist=tuple(
            ('color'+str(i),'input',{'width':200,'allchars':'num','maxchar':3,'charlist': () })
                for i in range(4)
            )
        kwargs.setdefault('title','Color:')
        self.maker_menu(flist,output_method,klass,val=ref,**kwargs)
