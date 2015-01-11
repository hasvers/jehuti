from gam_import import *




def claim_color(claimed):
        if type(claimed)==int:
            try:
                return user.ui.match.cast.get_info(user.ui.match.cast.actor_by_id[claimed])['color']
            except :
                return graphic_chart['player_colors'][claimed]
        if claimed== False or claimed is None:
            return 'unsaturated'
        if claimed == True:
            return (1.,1.,1.,1.)


class MatchArrow(Arrow):

    def make_surface(self,size,mod,infosource,*args,**kwargs):
        length=size[0]
        width=size[1]
        px = pg.PixelArray(pgsurface.Surface(size,Canvasflag))
        color_ext=graphic_chart['icon_node_fill_colors']
        logic = self.parent.logic
        t0=logic[0]
        t1=logic[1]
        const=array(logic[2:])

        info=infosource.get_info(self.parent.link)
        unsaturated=False
        if 'claimed' in info:
            if claim_color(info['claimed'])=='unsaturated':
                unsaturated =True
            else :
                mod = [i*j for i,j in zip(mod,claim_color(info['claimed']))]



        for x in range(length):
            for y in range(width):
                if abs(0.5- float(y)/width)  < float(width-x)*width/2/length/length:
                    tmp = [min([mod[i]* (1-(float(y)/width-.5)**2)* (color_ext[t0][i] + (color_ext[t1][i]-color_ext[t0][i])*(float(x)/length)) , 255]) for i in range(3)]
                    if unsaturated:
                        r,g,b= tmp
                        gray = (30*r+59*g+11*b)/100
                        tmp=[gray for i in xrange(3)]
                    px[x][y]= tuple(tmp+[255])
                else :
                    px[x][y]=COLORKEY
        surf= px.make_surface()

        if const.any():
            newsize=size
            suprec=array((graphic_chart['arrow_const'],0))
            if const[0]:
                newsize+=suprec
            #if const[1]:
                #newsize+=suprec
            img = pgsurface.Surface(newsize,pg.SRCALPHA)
            suprec[1]=width
            suprec[0]/=2
            suprec=pgrect.Rect((0,0), suprec)
            if const[0]:
                img.fill(color_ext[t0], suprec)
                img.blit(surf,(suprec.w*2,0))
            else:
                img.blit(surf,(0,0))
            if const[1]:
                suprec.right=img.get_rect().right
                img.fill(color_ext[t1], suprec)
        else:
            img=surf
        return img


class MatchNodeIcon(NodeIcon):

    def make_icon(self,size,radius,colors,val,unsaturated=False,mod=(1.,1.,1.,1.)):
        center=array(size)/2
        COLORKEY=(0,0,0,0)
        px = pg.PixelArray(pgsurface.Surface(size,pg.SRCALPHA))
        vpow=1.9
        iva=.5**-vpow
        newcols=[]
        for c in colors:
            if len(c)<4:
                c=c+(255,)
            newcols.append(c)
        colors=tuple(newcols)
        for x in range(size[0]):
            for y in range(size[1]):
                tup=(x-center[0],y-center[1])
                hyp =hypot(*tup)/radius
                if hyp>=1:
                    px[x][y]=COLORKEY
                elif pretty :
                    pixel=[0,0,0,0]
                    hyp2 =hypot(tup[0]+radius/5,tup[1]+radius/5)/radius/1.3
                    #maxy=center[1]+sqrt(radius**2-tup[0]**2)*cos((1+tanh(1.8*(val-0.5)))*pi/2.)
                    maxy=center[1]+sqrt(radius**2-tup[0]**2)*sin(-iva*copysign(abs(val)**vpow,val)*pi/2)
                    fy = float(y-maxy)/radius/2
                    if hyp < 1 :
                        for i in range(3):
                            shad=(1-.8*hyp2**3)*(1-.8 *hyp**3)*1.2
                            #if hyp2>0:
                                #shad/=hyp2
                            pixel[i]=min([mod[i]*rint( (colors[1][i]-colors[0][i])*(
                                1+tanh(20*fy))/2. + colors[0][i])*shad,255])
                        pixel[2]=min(255,pixel[2]+85*(1.-shad))
                        if unsaturated:
                            r,g,b=pixel[:3]
                            gray = (30*r+59*g+11*b)/100
                            pixel[:3]=[gray for i in xrange(3)]
                        #pixel[3]=min([rint(mod[3]*pixel[3]),255])
                        pixel[3]=min([mod[3]*rint( (colors[1][3]-colors[0][3])*( 1+tanh(20*fy))/2. + colors[0][3]),255])
                    else :
                        pixel=COLORKEY

                    px[x][y]=tuple(pixel)
                else :
                    if hyp<1:
                        px[x][y]=colors[1]
                    else :
                        px[x][y]=COLORKEY
        return px.make_surface()


    def make_surface(self,size,mod,infosource,*args,**kwargs):
        ringcolor = None
        unsaturated=False
        ringw=graphic_chart['node_ring_width']
        info =infosource.get_info(self.node)
        if 'claimed' in info:
            if type(info['claimed'])==int:
                ringcolor=claim_color(info['claimed'])
            else :
                if claim_color(info['claimed'])=='unsaturated':
                    unsaturated =True
                else :
                    mod = [i*j for i,j in zip(mod,claim_color(info['claimed']))]
                    ringcolor=tuple(int(i) for i in array(claim_color(True))*graphic_chart['claim_color'])

        radius = self.radius
        radius-=ringw
        center=array(size)/2
        val = info.get('truth',1.)-.5
        basesurf=CANVAS_ICON_LIB.get_icon('node',MatchNodeIcon,val=val,unsat=unsaturated)
        if basesurf:
            basesurf=pg.transform.smoothscale(basesurf,2*array((radius,radius)))
            surf=pgsurface.Surface(size ,pg.SRCALPHA)
            surf.fill((0,0,0,0))
            surf.blit(basesurf,center-(radius,radius))
        else:
            color_ext=graphic_chart['icon_node_fill_colors']
            surf=self.make_icon(size,radius,color_ext,val,unsaturated,mod)

        if ringcolor :
            pg.draw.circle(surf,ringcolor,center,radius+ringw,ringw)

        if 0 and user.debug_mode:
            ## node genre glyphs
            if 0 and 'subt' in info:
                nsum=max(2,3+rint(info['subt']*10))
                points=[center+radius*1.2*array((sin(z*2.*pi/nsum),cos(z*2.*pi/nsum))) for z in xrange(nsum)]
                pg.draw.polygon(surf,(25,25,255,255),points,2)
            if 'genre' in info:
                nsum=max(1,rint(info['subt']*10))
                try:
                    txt=image_load(database['image_path']+'icons/node/genres/'+info['genre'].lower()+str(nsum)+'.png')
                    txt1=pg.transform.smoothscale(txt,[rint(1.2*radius) for i in (0,1) ])
                    txt2=pg.transform.smoothscale(txt,[rint(1.2*radius-2) for i in (0,1) ])
                    txt=pgsurface.Surface(txt1.get_size(),pg.SRCALPHA)
                    txt.fill((128,128,128,128))
                    txt.blit(txt1,(0,0),None, pg.BLEND_RGBA_MIN)
                    txt.blit(txt2,(array(txt1.get_size())-txt2.get_size())/2)
                except:
                    txt=pgu_writen(info['genre'][:2]+str(nsum),FONTLIB["base"],graphic_chart['text_color_label'])
                surf.blit(txt,(array(size)-txt.get_size())/2)

        return surf#px.make_surface()

    def create(self,*args,**kwargs):
        #print 'create', self.item, user.evt.moving,time.time(), args[1],debug.caller_name()
        test=NodeIcon.create(self,*args,**kwargs)
        try:
            self.effects.keys()
        except:
            self.effects={}
        try:
            info=args[1]
        except:
            info=self.canvas.active_graph
        if info==self.canvas.active_graph:

            ieff=info.get_info(self.node,'effects')
            if ieff:
                self.clear_effects()
                for eff in ieff:
                    #if not eff in self.effects:
                    self.add_effect(eff)
                    #elif self.effects[eff] not in self.children:
                        #self.add_child(self.effects[eff])
                        #self.effects[eff].add_to_group(self.parent.tools)
            iterr=info.get_info(self.node,'terr')
            if iterr:
                self.set_terr(iterr)

        return test


    def anchor(self,logic,pos): #link_anchor
        return (self.rect.center)
        return(self.rect.midbottom,self.rect.midtop)[logic[pos]]

    def clear_effects(self):
        for eff,icon in tuple(self.effects.iteritems()):
            del self.effects[eff]
            icon.kill()
            if icon in self.children:
                self.children.remove(icon)
            if icon in self.floating:
                self.floating.remove(icon)
        self.effects={}


    def typ_area(self,relpos):
        #position relative to the CENTER of the icon
        #associated with anchors, to use them as hotspots
        if relpos[1]>0 :
            return 1
        else :
            return 0

    def add_effect(self,eff):
        em=CanvasIcon(self.parent)
        em.item=eff
        em.size=tuple(graphic_chart['effect_base_size'] for i in range(2))
        em.layer=4
        z=0
        if eff.val<0:
            z=1

        em.label=str(eff)
        em.color=graphic_chart['effect_color'][z]
        em.create(self.parent.group)
        self.add_child(em)
        em.add_to_group(self.parent.tools)
        self.effects[eff]=em

    def set_terr(self,terr):
        print 'terr',self,terr
        em=CanvasIcon(self.parent)
        em.item=self.item
        em.size=tuple(graphic_chart['effect_base_size'] for i in range(2))
        em.layer=4

        em.label='T:'+str(terr)
        em.color=graphic_chart['terr_color']
        em.create(self.parent.group)
        self.pos[em]=array([0,self.rect.h])
        self.add_child(em)
        em.add_to_group(self.parent.tools)

    def set_state(self,state,*args,**kwargs):
        if NodeIcon.set_state(self,state,*args,**kwargs):
            self.state_change()
            return True
        return False

    def state_change(self):
        pass
        #BAD IDEA: Impossible to hover over the effects
        #if not self.is_hovering:
            #for em in self.effects.values():
                #em.rem_from_group(self.parent.group)
        #else:
            #for em in self.effects.values():
                #em.add_to_group(self.parent.group)
        #if self.effects:
            #self.parent.dirty=1

    def rm_state(self,state,*args,**kwargs):
        if NodeIcon.rm_state(self,state,*args,**kwargs):
            self.state_change()
            return True
        return False



class MatchLinkIcon(LinkIcon):
    logic=None
    Arrow=MatchArrow

    def make_color(self,x,y,col0,col1):
        return (1-(y-.5)**2)* (col0 + (col1-col0)*(1+tanh(8*(x-0.5)))/2 )
        return min(  (255,test*0.8))

    def width(self,val):
        return max(int(floor(graphic_chart['link_base_width']*(0.2+val))),4)+2*graphic_chart['link_border_width']


    def create(self,*args,**kwargs):
        try:
            self.logic = args[1].get_info(self.link,'logic')
        except:
            pass
        return LinkIcon.create(self,*args,**kwargs)

    def make_surface(self,size,mod,infosource,*args,**kwargs):
        try:
            self.premade
        except:
            self.premade={}
        info=infosource.get_info(self.link)
        color_in=False
        bordercolor = None
        unsaturated=False
        borderw=graphic_chart['link_border_width']
        if 'claimed' in info:
            if type(info['claimed'])==int:
                bordercolor=claim_color(info['claimed'])
                if color_in :
                    tmp=[i/255. for i in bordercolor]
                    mod = [i*j for i,j in zip(mod,tmp)]
            else :
                if claim_color(info['claimed'])=='unsaturated':
                    unsaturated =True
                else :
                    mod = [i*j for i,j in zip(mod,claim_color(info['claimed']))]
                    bordercolor=tuple(int(i) for i in array(claim_color(True))*graphic_chart['claim_color'])

        blength,wid = size
        px = pg.PixelArray(pgsurface.Surface(size,Canvasflag))
        color_ext=graphic_chart['icon_node_fill_colors']
        t0=self.logic[0]
        t1= self.logic[1]
        desc=(color_ext[t0], color_ext[t1],bordercolor,color_in,tuple(mod),unsaturated)

        if desc in self.premade:
            return self.premade[desc].copy()

        if desc[0]==desc[1]:
            surf=pgsurface.Surface((blength,wid) )
            surf.fill(COLORKEY)
            if bordercolor:
                surf.fill(bordercolor)
            color=list(desc[0])
            if unsaturated:
                r,g,b=color[:3]
                gray = (30*r+59*g+11*b)/100
                color[:3]=(gray for i in range(3))
            surf.fill(color,pgrect.Rect(0,borderw,blength,wid-2*borderw) )
            self.premade[desc]=surf
            return surf
        for x in range(blength):
            for y in range(wid):
                if min(y,wid-y)<=borderw:
                    if bordercolor and color_in :
                        tmp= [self.make_color(float(x)/blength,float(y)/wid,color_ext[t0][i],color_ext[t1][i]) for i in range(3)]+[255]
                        px[x][y]=tuple(tmp)
                    elif bordercolor:
                        px[x][y]=bordercolor
                    else:
                        px[x][y]=COLORKEY
                else:
                    tmp= [self.make_color(float(x)/blength,float(y)/wid,color_ext[t0][i],color_ext[t1][i]) for i in range(3)]+[255]
                    if unsaturated:
                        r,g,b= tmp[:3]
                        gray = (30*r+59*g+11*b)/100
                        tmp[:3]=[gray for i in xrange(3)]
                    px[x][y]=(min(255,tmp[0]*mod[0]),min(255,tmp[1]*mod[1]),min(255,tmp[2]*mod[2]),min(255,tmp[3]*mod[3]))
        surf=self.premade[desc]=px.make_surface()
        return surf

class ExplorerBeacon(SignalBeacon):
    draggable=True
    layer = 0
    def __init__(self,canvas,evt):
        if evt.radius<1.: #fractional
            self.radius=int(evt.radius*min(canvas.rect.size))
        else :
            self.radius=int(evt.radius)

        signal=Signal('kill',evt, source='beacon')
        self.size=(2*self.radius,2*self.radius)
        SignalBeacon.__init__(self,canvas,signal)
        self.neigh=[]
        self.item=evt
        #self.label='Exploration radius'
        self.label=''

    def find_neighbors(self):
        self.neigh=[]
        for n in self.canvas.nodes:
            if pgsprite.collide_circle(n,self):
                self.neigh.append(n.item)
        return self.neigh

    def make_surface(self,size,mod,infosource,*args,**kwargs):
        surf=pgsurface.Surface(self.size,pg.SRCALPHA)
        surf.fill(COLORKEY)
        ringw=2
        radius = self.radius
        center=(radius,radius)
        pg.draw.circle(surf,(255,255,255,40),center,radius-ringw)
        pg.draw.circle(surf,(255,255,255,100),center,radius,ringw)
        pg.draw.circle(surf,(255,255,255,100),center,8,0)
        return surf
