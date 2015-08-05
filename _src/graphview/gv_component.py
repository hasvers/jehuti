# -*- coding: utf-8 -*-

#The base library contains only one component : the Graph-Canvas compound.
#Nevertheless, components are the proper way of handling the tripartition Data - View - Handler
#while allowing multiple relationships between views and data


from gv_data import *

from gv_ui_complete import *

class View(UI_Widget):

    bg=False
    viewport=None
    name=''
    offset=(0,0)

    def __init__(self,handler,parent=None):
        super(View, self).__init__()
        self.actions={'hover':True,'select':True}
        self.handler=handler
        self.parent = parent
        self.icon={}
        self.group=pgsprite.LayeredUpdates()
        self.animated=pgsprite.Group()

    def renew(self):
        self.kill(True)
        self.icon={}
        self.animated.empty()
        self.group.empty()


    def update(self):
        [c.update() for c in self.children]

    def paint(self,surface=None):
        self.group.update()
        if not surface:
            surface=self.suface
            self.surface.fill(COLORKEY)
        if self.bg :
            surface.blit(self.bg,(0,0))
        if self.viewport:
            viewport=self.viewport.move(self.offset)
        else:
            viewport=None
        for s in self.group :
            if not viewport or s.rect.colliderect(viewport):
                surface.blit(s.image,s.rect)
        for c in self.children:
            if hasattr(c,'paint'):
                c.paint(surface)


    def event(self,event,**kwargs):
        for c in self.children :
            if c.event(event,**kwargs):
                return True
        return False

    def select(self,*args,**kwargs):
        #standard mouse action
        if not self.actions['select']:
            return False
        if UI_Widget.select(self,*args) :
            if kwargs.get('source',None)!=self.handler:
                if self.selected :
                    self.handler.select(self.selected.item)
                else :
                    self.handler.unselect()
            return True
        return False

    def unselect(self,*args,**kwargs):
        if UI_Widget.unselect(self,*args) :
            if kwargs.get('source',None)!=self.handler :
                self.handler.unselect()
            return True
        return False

    def hover(self,hover,**kwargs) :
        if not self.actions['hover']:
            return False
        if UI_Widget.hover(self,hover):
            if kwargs.get('source',None)!=self.handler:
                self.handler.hover(hover.item)
            return True
        return False

    def unhover(self,**kwargs):
        if UI_Widget.unhover(self):
            if kwargs.get('source',None)!=self.handler:
                self.handler.unhover()
            return True
        return False


    def mousepos(self,child=None):
        return tuple(array(UI_Widget.mousepos(self,child))+array(self.offset))

class Handler(object):
#Handles any change or event, be it caused by the user or any other source

    master=False
    name=''
    View=View
    Data=Data
    #A master component is a direct child of the UI (Window manager)
    #A slave component sends everything to its parent for preprocessing
    #and should never call windows directly

    def __init__(self,parent=None,**kwargs):
        self.parent = parent
        self.depend=DependencyGraph()
        self.data=kwargs.get('data',None)
        if self.data is None:
            self.data=self.Data()
        if hasattr(parent,'view'):
            pview=parent.view
        else:
            pview=parent
        self.view=kwargs.get('view',None)
        if self.view is None:
            self.view=self.View(self,pview)
        self.view.handler=self

    def get_info(self,*args,**kwargs):
        return self.data.get_info(*args,**kwargs)

    def set_info(self,*args,**kwargs):
        return self.data.set_info(*args,**kwargs)

    @property
    def group(self):
        return self.view.group

    def menu(self,*args,**kwargs):
        return ()

    def call_menu(self,menu,*args,**kwargs):
        if not menu:
            menu=self.menu()
        if not menu:
            return False
        if self.master:
            self.parent.float_menu(menu,oneshot=True,**kwargs)
        else:
            self.parent.call_menu(menu,*args,**kwargs)

    def signal(self,signal,*args,**kwargs):
        kwargs.setdefault('affects',self)
        event=Event(*args,type=signal,source=self.name,**kwargs)
        if user.ui:
            user.evt.pass_event(event,self,True)


    def update(self):
        self.view.update()
        return

    def event(self,event,**kwargs):
        return self.view.event(event,**kwargs)

    def make_dependencies(self):
        self.depend.clear()
        self.depend.add_dep(self,self.data)

    def set_data(self,data):
        self.data=data
        self.renew()

    def renew(self):
        self.depend=DependencyGraph()
        self.make_dependencies()
        return True

    def react(self,evt):
        if 'select' in evt.type :
            if hasattr(evt,'item') and evt.item in self.view.icon:
                #if not hasattr item, it is a signal, not a SelectEvt, so it should be disregarded
                icon=self.view.icon[evt.item]
                if evt.state==1 and not icon.is_selected:
                    UI_Widget.select(self.view,icon)
                    return True
                if evt.state==0 and icon.is_selected:
                    UI_Widget.unselect(self.view,icon)

        return False


    def set_from_file(self,filename,**kwargs):
        genre=self.data.datatype
        path=database['{}_path'.format(genre)]
        ext=database['{}_ext'.format(genre)]
        print 'Setting {} from'.format(genre),filename
        #if not ext in filename:
            #fin = fopen(path+filename+ext, "rb" )
        #else :
            #fin = fopen(filename, "rb")
        #data = pickle.load( fin)
        try:
            data=self.data()
        except:
            data=self.data.__class__()
        data.txt_import(filename)
        #fin.close()
        if kwargs.get('initial',False):
            self.data=data
        else:
            return self.set_data(data)

    def save_to_file(self,filename,data=None):
        if data is None:
            data=self.data
        data.name=filename
        data.save()

    def make_children_handlers(self,typs,handlers,**kwargs):
        #For complex handlers
        for i in typs:
            j=handlers[i]
            ar=self,
            kw=dict((k,kwargs[k][i]) for k in kwargs if i in kwargs[k])
            setattr(self,i, j(*ar,**kw) )
            if not 'view' in kw:
                kw['view']=getattr(self,i).view
            kw['view'].parent=self.view
            kw['view'].handler=getattr(self,i)
            self.view.children.append(kw['view'])

    def select(self,item):
        self.signal('select',item)
        return 1

    def unselect(self):
        self.signal('unselect')
        return 1

    def hover(self,item):
        self.signal('hover',item,label=self.label(item,'hover'),affects=(self,item))
        return 1

    def unhover(self,**kwargs):
        self.signal('unhover')
        return 1
