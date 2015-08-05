from gv_ui_complete import *


class CanvasIcon(UI_Icon):
    state_list=('idle','hover','select')
    sound=True
    def __init__(self,canvas=None):
        super(CanvasIcon, self).__init__()
        if canvas:
            self.canvas=canvas
            self.id=canvas.id
            canvas.id+=1

    #def set_state(self,*args,**kwargs):
        #if UI_Icon.set_state(self,*args,**kwargs):
            #if self.parent:
                #self.parent.dirty=1
            #return True
        #return False
    #def rm_state(self,*args,**kwargs):
        #if UI_Icon.rm_state(self,*args,**kwargs):
            #if self.parent:
                #self.parent.dirty=1
            #return True
        #return False

    def event(self,event,**kwargs):
        return False #  self.canvas.handler.event(event)

    def make_circle(self,size,color,mod=(1,1,1,1) ):
        px = pg.PixelArray(pgsurface.Surface(size,Canvasflag))
        radius = min(size[0],size[1])*.5
        center=array(size)*.5
        for x in range(size[0]):
            for y in range(size[1]):
                tup=(x-center[0],y-center[1])
                hyp =hypot(*tup)/radius
                if pretty :
                    pixel=[0,0,0,0]
                    hyp2 =hypot(tup[0]+radius/5,tup[1]+radius/5)/radius/1.3
                    if hyp < 1 :
                        for i in range(3):
                            pixel[i]=min([mod[i]*color[i]*(1-.8*hyp2**3)*(1-.8 *hyp**3)*1.2,255])
                        pixel[3]=min([mod[3]*255,255])
                    else :
                        pixel=COLORKEY

                    px[x][y]=tuple(pixel)
                else :
                    if hyp<1:
                        px[j][x][y]=color
                    else :
                        px[j][x][y]=COLORKEY
        return px.make_surface()

    def make_surface(self,size,mod,*args,**kwargs):
        color=kwargs.get('color',False)
        if not color and hasattr(self,'color'):
            color=self.color
        if not color:
            color=(180,180,180,255)
        return self.make_circle(size,color,mod)

    def debug(self):
        if hasattr(self,'item'):
            return self.canvas.get_info(self.item)
        return None

class SignalBeacon(CanvasIcon):
    #Icons for signals, events and the like (in case I want to place items on the canvas that may send a signal)
    label=''
    size=(32,32)
    def __init__(self,canvas,signal):
        self.signal=signal
        if not self.label:
            self.label='Signal beacon: '+str(signal)
        CanvasIcon.__init__(self,canvas)
        self.canvas.tools.add(self)
        self.type='beacon'
        self.img_init()

    def img_init(self):
        self.image=pgsurface.Surface(self.size)
        self.image.fill(COLORKEY)
        self.rect=self.image.get_rect()
        self.rect.topleft = 0,0
        self.radius=min(self.rect.size)/2
        self.size=self.rect.size

    def make_surface(self,size,mod,infosource,*args,**kwargs):
        surf=pgsurface.Surface(self.size,pg.SRCALPHA)
        surf.fill(COLORKEY)
        radius = self.radius
        center=(radius,radius)
        pg.draw.circle(surf,(255,255,255,40),center,radius)
        return surf


    def create(self,group=None,infosource=None):
        if not infosource :
            infosource = self.canvas.active_graph
        CanvasIcon.create(self,group,infosource)


    def event(self,event,*args,**kwargs):
        #if event.type == pg.MOUSEBUTTONDOWN and event.button==1:
        #    return self.signal #self.canvas.handler.signal(self.signal,beacon=self)
        return False


class Arrow(CanvasIcon):
    mutable=True
    layer = 0

    def make_surface(self,size,mod,cset,*args,**kwargs):
        length=size[0]
        width=size[1]
        px = pg.PixelArray(pgsurface.Surface(size,Canvasflag))
        for x in range(length):
            for y in range(width):
                if abs(0.5- float(y)/width)  < float(width-x)*width/2/length/length:
                    px[x][y]=tuple([min(mod[i]* 190 ,255)for i in range(4)])
                else :
                    px[x][y]=COLORKEY
        return px.make_surface()

    def create(self,group=None,parent=None):
        self.parent = parent
        self.set=parent.set
        val = self.canvas.get_info(parent.link,'val')
        if not val:
            val=0.
        lwid= graphic_chart['link_base_width']
        self.size=(lwid*2,int(lwid*(1.5 + val/2)))
        CanvasIcon.create(self,group,self.set)


class NodeIcon(CanvasIcon):
    draggable=True
    layer = 1
    def __init__(self,canvas=None,node=None):
        if not canvas or not node:
            pass
        else:
            CanvasIcon.__init__(self,canvas)
            canvas.nodes.add(self)
            self.ilinks=[]
            self.node=self.item=node
            self.rect_init()


    def rect_init(self,center=None):
        val = self.canvas.get_info(self.node,'val')
        dft_size=tuple(int(graphic_chart['node_base_size']*(val+0.25)) for i in (1,1) )
        self.rect=pgrect.Rect((0,0),dft_size)
        if center :
            self.rect.center=center
        self.radius=min(self.rect.size)/2
        self.size=self.rect.size


    def make_surface(self,size,mod,infosource,*args,**kwargs):
        #px = pg.PixelArray(pgsurface.Surface(size,Canvasflag))
        #radius = self.radius
        #center=(radius,radius)
        color_ext=graphic_chart['icon_node_fill_colors']
        val=infosource.get_info(self.node,'color')
        if val==False :
            val = 0.
        return self.make_circle(size,(array(color_ext[1])-color_ext[0])*val + color_ext[0],mod)

        #for x in range(size[0]):
            #for y in range(size[1]):
                #tup=(x-center[0],y-center[1])
                #hyp =hypot(*tup)/radius
                #if pretty :
                    #pixel=[0,0,0,0]
                    #hyp2 =hypot(tup[0]+radius/5,tup[1]+radius/5)/radius/1.3
                    #if hyp < 1 :
                        #for i in range(3):
                            #pixel[i]=min([mod[i]*int( (color_ext[1][i]-color_ext[0][i])*val + color_ext[0][i])*(1-.8*hyp2**3)*(1-.8 *hyp**3)*1.2,255])
                        #pixel[3]=min([mod[3]*255,255])
                    #else :
                        #pixel=COLORKEY

                    #px[x][y]=tuple(pixel)
                #else :
                    #if hyp<1:
                        #px[j][x][y]=color_ext[1]
                    #else :
                        #px[j][x][y]=COLORKEY

        #return px.make_surface()


    def create(self,group =None,infosource=None):

        if not infosource :
            infosource = self.canvas.active_graph
        if infosource == 'all':
            for s in self.image_sets.keys():
                if not s in self.parent.state or self.parent.state[s]=='hidden':
                    self.set_to_create.add(s)
                    continue
                self.create(group,s)
            return True
        if infosource== self.canvas.active_graph:
            for c in self.children :
                c.kill()
            del self.children[:]
        if not self.set :
            self.set = infosource

        self.rect_init(self.rect.center)
        CanvasIcon.create(self,group,infosource)

        '''
        font = pg.font.Font(None, int(radius*1.25))
        text = font.render(str(self.id), 1, (150, 120, 120))
        trect=text.get_rect()
        self.base_image.blit(text, (center[0]-trect.center[0],center[1]-trect.center[1]))

        text = font.render(str(self.id), 1, (100, 60, 90))
        trect=text.get_rect()
        self.selected_image.blit(text, (center[0]-trect.center[0],center[1]-trect.center[1]))
        '''

    def set_pos(self,pos):
        self.rect.center=pos
        self.canvas.pos[self.node]=array(pos)
        [l.follow_anchors() for l in self.ilinks]

    def drag(self,rel):
        rect = self.rect.move(rel)
        bound=self.canvas.rect
        if bound.contains(rect):
            self.rect.move_ip(rel)
            self.canvas.pos[self.node]=array(self.canvas.pos[self.node])+array([int(i) for i in rel])
        [l.follow_anchors() for l in self.ilinks]
        self.update()
        self.canvas.dirty=1

    def anchor(self,genre,pos):
        #where should a link attach itself on the node, depending on the link's
        #genre and whether this node is source or target (pos 0 or 1)
        return (self.rect.center)

    def typ_area(self,relpos):
        #position relative to the CENTER of the icon
        #associated with anchors, to use them as hotspots
        return False



class LinkIcon(CanvasIcon):
    mutable=True
    layer = 0
    arrow=None
    Arrow=Arrow

    def __init__(self,canvas,link,parents):
        CanvasIcon.__init__(self,canvas)
        canvas.links.add(self)

        self.link=self.item=link
        self.rect=pgrect.Rect((0,0),(20,20))
        self.rect.topleft = 0,0
        self.parents = tuple(parents)

    def upd_child(self):
        return False

    def width(self,val):
        return max(int(floor(graphic_chart['link_base_width']*(0.2+val))),4)

    def make_surface(self,size,mod,cset,*args,**kwargs):
        blength,wid = size
        px = pgsurface.Surface(size,Canvasflag)
        px.fill(tuple( ( min(255,190*l) for l in mod)))
        return px

    def color_mod(self,state):
        return graphic_chart.get('link_'+state+'_color_mod',CanvasIcon.color_mod(self,state))

    def create(self,group=None,infosource=None):


        if not infosource :
            infosource = self.canvas.active_graph
        if infosource == 'all':
            for s in self.image_sets.keys():
                if not s in self.parent.state or self.parent.state[s]=='hidden':
                    self.set_to_create.add(s)
                    continue
                self.create(group,s)
            return True
        self.genre = infosource.get_info(self.link,'genre')
        if not self.set :
            self.set = infosource

        val=infosource.get_info(self.link,'val')
        if not val:
            val=0
        self.wid=wid= self.width(val)
        #for c in self.children :
        #    c.kill()
        del self.children[:]
        #self.arrow=False

        self.parents[0].update()
        self.parents[1].update()
        x1,y1=self.parents[0].anchor(self.genre,0)
        x2,y2=self.parents[1].anchor(self.genre,1)
        blength = max(int(hypot(x2-x1,y2-y1)),10)
        self.size=(blength,wid)

        CanvasIcon.create(self,group,infosource)

        if not self.arrow :
            self.arrow=self.Arrow(self.canvas)
            self.arrow.set=self.set
        self.children.append(self.arrow)
        self.arrow.create(group,self)

        self.follow_anchors()

    def follow_anchors(self):

        x1,y1=self.parents[0].anchor(self.genre,0)
        x2,y2=self.parents[1].anchor(self.genre,1)
        r1,r2=tuple([p.radius for p in self.parents])
        blength = max(int(hypot(x2-x1,y2-y1)),1)
        wid=self.wid
        lcos = float(x2-x1)/blength
        lsin = float(y1-y2)/blength
        angle =  atan2(lsin,lcos)*360/pi/2.0

        self.size= (blength,wid)
        for ic in (self,self.arrow):
            if ic.angle != angle :
                ic.angle=angle
            else :
                ic.mutate()

            #newimg = pg.transform.scale(ic.images[self.state],ic.size)
            #Idee pour remplacer layers, mais probleme des autres nodes superposes aux extremites
            #pg.draw.circle(newimg,(0,0,0,0),(0,wid/2),r1)
            #pg.draw.circle(newimg,(0,0,0,0),(blength,wid/2),r2)
            #ic.image = pg.transform.rotate(newimg,angle)
            ic.rect=ic.image.get_rect()
            ic.rect.center=((x2-x1)/2+x1,(y2-y1)/2+y1)


    def set_state(self,state,force_redraw=False,**kwargs):
        if CanvasIcon.set_state(self,state,force_redraw,**kwargs) :
            self.arrow.set_state(state,force_redraw,**kwargs)
            return True
        return False


    def rm_state(self,state,force_redraw=False,**kwargs):
        if CanvasIcon.rm_state(self,state,force_redraw,**kwargs) :
            self.arrow.rm_state(state,force_redraw,**kwargs)
            return True
        return False

    def kill(self):
        for p in self.parents :
            p.ilinks.remove(self)
        return CanvasIcon.kill(self)



class LinkGrabber(NodeIcon):
    draggable=True
    layer = 0
    ID=None
    def __init__(self,canvas):
        self.trueID='LinkGrabber'
        self.name='LinkGrabber'
        self.image_sets={}
        self.set=None
        UI_Item.__init__(self)
        self.type='tool'
        self.ilinks=[]
        self.canvas=canvas
        self.image=pgsurface.Surface((4,4))
        self.rect=self.image.get_rect()
        self.rect.topleft = 0,0
        self.radius=min(self.rect.size)/2

    def rm_state(self,state,force_redraw=False,**kwargs):
        return True

    def set_state(self,state,force_redraw=False,**kwargs):
        return True

    def drag(self,rel):
        rect = self.rect.move(rel)
        bound=self.canvas.rect
        if bound.contains(rect):
            self.rect.move_ip(rel)
        [l.follow_anchors() for l in self.ilinks]
        self.canvas.dirty=1

    def event(self,event,**kwargs):
        if event.type == pg.MOUSEBUTTONDOWN:
            return self.canvas.handler.end_linkgrabber(self,event)
        if event.type == pg.MOUSEMOTION:
            pos = self.canvas.handler.mousepos()
            rate=ergonomy['nodes_stickyness_to_mouse']
            rel=(event.rel[0]+(pos[0]-self.rect.center[0])*rate,event.rel[1]+(pos[1]-self.rect.center[1])*rate)
            self.drag(rel)
#            self.canvas.update()
        return True

    def kill(self):
        return UI_Item.kill(self)

