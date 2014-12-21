# -*- coding: utf-8 -*-
from gam_graph import *
from gam_canvasicons import *
from gam_script_base import FuncWrapper


class LogicCanvas(Canvas):
    Graph=MatchGraph
    NodeIcon=MatchNodeIcon
    LinkIcon=MatchLinkIcon
    def react(self,evt):
        self.handler.react(evt)
        #except:
         #   pass
        if 'change_infos' in evt.type:
            if array( [i in evt.infos for i in ('val','genre','logic','truth','claimed','effects','subt','terr') ]).any():
                target=evt.item
                self.icon_update(target)
            return True
        return Canvas.react(self,evt)

class LogicCanvasHandler(CanvasHandler):
    def truth_calc(self, item,graph=None,sub=None,track=None,tracklist=None):
        #Call whenever bias changes or new link added, to recompute truth
        #track allows to track logical cycles
        if track is None:
            track={}
            tracklist=[]
        match=self.parent.handler
        srceff=match.ruleset.link_effect_from_source
        tgteff=match.ruleset.link_effect_from_target
        if graph is None:
            graph=self.canvas.active_graph
        if sub is None:
            sub=graph
        if item.type=='link':
            s,t=item.parents
            logic=graph.get_info(item,'logic')
            if srceff(graph.get_info(s,'truth'),logic ):
                return self.truth_calc(t,graph,sub,track,tracklist)
            elif tgteff(graph.get_info(t,'truth'),logic ):
                return self.truth_calc(s,graph,sub,track,tracklist)

        truth=match.ruleset.calc_truth(item,graph,sub,extrapolate=0)
        prevtruth=graph.get_info(item,'truth')
        #print 'glappy:', item,graph.name,sub.name,truth,prevtruth
        if truth==prevtruth:
            return 0
        if item in track:
            basetruth=track[item][0]
            assert track[item][1]==prevtruth #else there is something strange going on
            if truth==basetruth or (truth-basetruth)*(prevtruth-basetruth)<0:
                if truth==basetruth:
                    print 'alternating circle'
                print 'reductio ad absurdum'
                #reductio ad absurdum: the initial change causes a contradiction, cancel all changes
                #cancel
                for i in tracklist[tracklist.index(item):]:
                    if sub.get_info(i,'truth')!=track[i][0]:
                        self.canvas.change_infos(i,graph=sub,truth=track[i][0],invisible=True,source='truthcalc')
                        track[i]=(track[i][0],track[i][0])
                return 0
            else:
                if abs(truth-basetruth)>abs(prevtruth-basetruth):
                    print 'diverging cycle'
                    #virtuous circle, will saturate at 0 or 1, might as well set it right now
                    #unless more changes are to come (truth_value is changed by the circle)
                    if match.ruleset.truth_value(truth)== match.ruleset.truth_value(prevtruth):
                        nt=(1.+match.ruleset.truth_value(truth))/2
                        self.canvas.change_infos(item,graph=sub,truth=nt,invisible=True,source='truthcalc')
                        track[item]=(basetruth,nt)
                        return 0
                else:
                    print 'converging cycle', basetruth,prevtruth,truth
                    #attenuating effect, will converge, no problem
        self.canvas.change_infos(item,truth=truth,graph=sub,invisible=True,source='truthcalc')
        #print 'set truth',item.name,truth, 'from' ,prevtruth, 'in', graph.name
        track[item]=(prevtruth,truth)
        tracklist.append(item)
        if match.ruleset.truth_value(truth)!= match.ruleset.truth_value(prevtruth):
            for l in sub.links.get(item,[]):
                logic=sub.get_info(l,'logic')
                if l.parents[0]==item:
                    if srceff(truth,logic)!=srceff(prevtruth,logic):
                        self.truth_calc(l.parents[1],graph,sub,track,tracklist)
                elif tgteff(truth,logic)!=tgteff(prevtruth,logic):
                    self.truth_calc(l.parents[0],graph,sub,track,tracklist)
        return 1

    def react(self,evt):
        if  'add' in evt.type  or 'change' in evt.type and True in [x in evt.infos for x in ('bias' ,'logic','val')]:
            for gph in self.canvas.layers:
                if gph.contains(evt.item):
                    self.truth_calc(evt.item,gph)

class LogicCanvasEditor(CanvasEditor,LogicCanvasHandler):
    #Generic canvas editor for matchs, beliefs

    def maingraph_menu(self,target,typ,event=None):
        if typ == 'node':
            if not ergonomy['edit_on_select']:
                struct=('Edit',lambda t=target:self.signal('edit',t)),
            else :
                struct=()
            logic = target.typ_area(array(self.mousepos())-array(target.rect.center))
            struct +=( ('Add link',lambda: self.start_linkgrabber(target,logic)),
            ('Delete node',lambda: self.rem_node(target.node)),
            ('Fast quote',lambda: self.make_quote(target.node))
            )
            return struct
        return CanvasEditor.maingraph_menu(self,target,typ,event)

    def subgraph_menu(self,target,typ,event=None):
        struct= CanvasEditor.subgraph_menu(self,target,typ,event)
        if typ=='node':
            target=target.item
            gph=self.canvas.active_graph
            if gph.contains(target) and gph.links[target]:
                t=self.parent.handler.ruleset.calc_truth(target,gph,gph)
                if t!= gph.get_info(target,'truth'):
                    lamb=lambda:self.canvas.change_infos(target,truth=t)
                    struct+= ('Derive logic',lamb),
        return struct

    def start_linkgrabber(self,source,logic=None):
        if logic==None :
            logic = 1
        CanvasEditor.start_linkgrabber(self,source,logic=(logic,2,0,0))

    def end_linkgrabber(self,grabber,event):
        user.ungrab()
        #newevent=pgevent.Event( pg.MOUSEMOTION,pos=self.mousepos(),rel=(0,0))
        #self.event(newevent)
        self.test_hovering(event)
        if isinstance(self.hovering,self.canvas.NodeIcon):
            for i in grabber.ilinks :
                newp=[self.hovering.node if p==grabber else p for p in i.link.parents]

                if newp[0]!=newp[1]:
                    #self.canvas.rewire(i.link,tuple(newp))
                   # i.rm_state('ghost')
                    infos=self.canvas.get_info(i.link)
                    logic = self.hovering.typ_area(array(self.mousepos())-array(self.hovering.rect.center))
                    logic=(self.canvas.get_info(i.link,'logic')[0],logic,0,0)
                    infos['logic']=logic
                    self.canvas.remove(i.link)
                    act=self.canvas.active_graph
                    evt = AddEvt(act.Link(tuple(newp)),act,infos=infos )
                    user.evt.do(evt,self)

                    #self.canvas.change_infos(i.link,logic=logic,invisible=True)
                else :
                    self.canvas.remove(i.link)

        else :
            for i in grabber.ilinks:
                self.canvas.remove(i.link)
        grabber.kill()

        return True

    def bgmenu(self,main=True):
        if main :
            bgmenu=[]

            bgmenu += [ ('Add node',lambda p=self.mousepos() :self.add_node(None,None,pos=p))
                ]
            if not user.ui.view['nodelist']:
                bgmenu += [('Node list',lambda:user.ui.show('nodelist') )]
        else :
            act = self.canvas.active_graph
            bgmenu = [
                ('Randomize bias',lambda e=act: self.randomize_graph(e,'bias',(-.5,.5),uniform=True)),
                ]

        return bgmenu

    def randomize_graph(self,graph,info_type,rset,**kwargs):
        item_type=kwargs.pop('item_type',False)
        evt=Event(desc='Randomize',type='randomize_{}'.format(info_type))
        for i in graph.infos :
            if not item_type or i.type== item_type :
                if kwargs.get('uniform',False):
                    choice = rnd.uniform(*rset)
                elif kwargs.get('randint',False):
                    choice = rnd.randint(*rset)
                else :
                    choice = rnd.choice(rest)
                cevt=ChangeInfosEvt(i,graph,**{info_type:choice})
                evt.states.node[1]['children_states'][cevt]=1
                evt.states.node[0]['children_states'][cevt]=0

        if 'truth' ==info_type :
            for i, icon in self.canvas.icon.iteritems():
                if i.type=='node':
                    icon.create(self.canvas.group,'all')
        user.evt.do(evt)


    def fast_edit(self,target,event):
        #using the mousewheel fo fast edit
        try:
            item=target.item
        except:
            return False
        if event.button==4:
            d=1
        elif event.button==5:
            d=-1
        if pg.key.get_pressed()[pg.K_m]:
            if item.type in ('node','link'):
                self.canvas.change_infos(item,val=d*.05,additive=True)
                return True
        if pg.key.get_pressed()[pg.K_t]:
            if item.type in ('node') and 'bias' in self.canvas.get_info(item):
                self.canvas.change_infos(item,bias=d*.05,additive=True)
                return True
        if pg.key.get_pressed()[pg.K_s]:
            if item.type in ('node','link'):
                self.canvas.change_infos(item,subt=d*.05,additive=True)
                return True
        if pg.key.get_pressed()[pg.K_g]:
            if item.type in ('node',):#'link'):TODO link genre is either pattern or logic
                genres=database[item.type+'_genres']
                g=genres[(genres.index(self.canvas.get_info(item,'genre'))+d)%len(genres)]
                self.canvas.change_infos(item,genre=g)
                return True
        if pg.key.get_pressed()[pg.K_i]:
            act=self.canvas.active_graph
            if item.type in ('node','link') and act.parent==self.canvas.graph:
                if not act.contains(item):
                    self.add_node(item,layer=act,addrequired=True,assess=True)
                else:
                    self.rem_node(item,layer=act,addrequired=True,assess=True)
                return True
        return False

    def make_quote(self,item):
        info=self.canvas.get_info(item)
        name=info['name']
        for v in text_bank['templateverbs']:
            name=name.replace(' {} '.format(v),' {'+v+'} ')
        quote=ConvNodeTest(value=name[0].lower()+name[1:],truth='+',cond='Alone')
        self.canvas.change_infos(item,quotes=[quote],update=True)

    def label(self,item):
        try:
            return item.label
        except:
            pass
        if hasattr(item,"item"): #if we receive an icon
            item=item.item
        infos = self.canvas.get_info(item)
        if item.type=='node':
            return  'N{}: {} - {}'.format(item.ID,infos['name'],infos['desc']) #+ ' T:'+str(infos.get('terr',0))#+ ': '+ infos['desc']
        elif item.type=='link':
            return  str([i.ID for i in item.parents])+infos['pattern'] #+ ': '+ infos['desc']

class MatchCanvas(LogicCanvas):
    pass

class MatchCanvasHandler(LogicCanvasHandler):
    pass

class MatchCanvasEditor(LogicCanvasEditor,MatchCanvasHandler):
    def react(self,evt):
        if  'add' in evt.type  or 'change' in evt.type and True in [x in evt.infos for x in ('bias' ,'logic','val')]:
            for gph in self.parent.handler.data.actorgraph.values():
                if gph.contains(evt.item):
                    self.truth_calc(evt.item,gph)


class MatchCanvasPlayer(MatchCanvasHandler):
    select_opt=deepcopy(MatchCanvasHandler.select_opt)
    select_opt['default_multi']=True
    select_opt['auto_unselect']=False
    def __init__(self,canvas,parent,size=None):
        MatchCanvasHandler.__init__(self,canvas,parent,size)
        self.fog=FogOfWar(self)
        self.events=[]
        self.human_player= True #Can the user act (play) on the canvas?
        #self.canvas.group.add(self.fog,layer=4)

    def set_circle(self,center,radius,**kwargs):
        self.fog.remove_circle(center,radius)
        move= kwargs.get("move",None)
        if move=='empty':
            move=len(self.canvas.motion)==0
        if move:
            self.center_on(center,kwargs.get('glide',1))

    def paint(self,surface=None):
        MatchCanvasHandler.paint(self,surface)

        offset=self.offset
        offset=(-offset[0],-offset[1])
        surface.blit(self.fog.image,offset)

    def label(self,item):
        try:
            return item.label
        except:
            pass
        if hasattr(item,"item"): #if we receive an icon
            item=item.item
        infos = self.canvas.get_info(item)
        if item.type=='node':
            if infos['desc']:
                return '{} - {}'.format(infos['name'],infos['desc'])
            #if database['edit_mode']:
                #return  '{} {}'.format(infos['name'],infos['truth'])
            else:
                return  '{}'.format(infos['name'])#,rfloat(infos['bias']),rfloat(infos['truth'])) #+ ' T:'+str(infos.get('terr',0))#+ ': '+ infos['desc']
        elif item.type=='link':
            return  infos['pattern'] #+ ': '+ infos['desc']

    def drag(self):
        return False

    def event(self,event,**kwargs):
#        self.fog.update()
        #print self.fog.mask.get_at(self.mousepos()),self.fog.mask.get_at((0,0))
        #print self.fog.mask.get_at(self.mousepos())
        if  event.type == pg.MOUSEBUTTONDOWN and self.fog.mask.get_at(self.mousepos()) :
            target= self.hovering
            if target and target.item.type=='node':
                print 'TMP',target.item
            return False
        return MatchCanvasHandler.event(self,event,**kwargs)


    def menu(self,event=None):
        target= self.hovering
        if not target:
            typ='bg'
        else :
            typ=target.item.type
        if self.human_player and (self.parent.handler.time_left>0 or database['allow_overtime']):
            if typ == 'node':
                match=self.parent.handler #TODO: this is unclean
                out=lambda e: self.signal('ponder',target,cost=e)
                pmin=match.ruleset.pondermin
                maxval=max(pmin,match.time_left-match.time_cost)
                if maxval>pmin:
                    lampon=lambda:user.ui.input_menu('drag',out,title='Time:',
                        minval=pmin,maxval=maxval,showval=0,val=maxval)
                else:
                    lampon=lambda: out(pmin)
                struct=()
                struct +=( ('Ponder',lampon,
                        'Ponder: Explore mental space.'),
#                    ('Fallacy',lambda : self.signal('fallacy',target),
 #                       'Fallacy: Fabricate argument.'),
                    )
                act= match.active_player
                if match.cast.get_info(act,'path'):
                    gph=match.data.actorsubgraphs[act][act]
                    if self.canvas.active_graph ==gph :
                        struct+=('Pathos (self)',lambda : self.signal('pathos_signal_self',target),
                            'Invest emotional territory.'),
                    else :
                        struct+=('Pathos (other)',lambda : self.signal('pathos_signal_other',target),
                            'Induce emotional investment in hearer.'),


                return struct
            if typ == 'link' :
                return ()
            if typ == 'bg' :
                return self.bgmenu()
        return ()

    def bgmenu(self,main=True):
        bgmenu=()
        return bgmenu



    def select(self,target,*args,**kwargs):

        for e in self.events:
            if e.type=='select' and e.item==target:
                self.events.remove(e)
                if e.state==1:
                    user.evt.undo(e)
                    return True
        evt=SelectEvt(target,affects=[self.canvas,self],**kwargs)
        user.evt.do(evt)
        self.events.append(evt)
        return True
        #return MatchCanvasHandler.select(self,target,*args,**kwargs)


    def keymap(self,event,**kwargs):
        pos = kwargs.get('pos',None)
        if event.key == pg.K_TAB :
            return 0
        return MatchCanvasHandler.keymap(self,event,**kwargs)

    def react(self,evt):
        #print '==flu'
        match=self.parent.handler
        if 'hyperlink' in evt.type :
            #print 'canvas received',evt,evt.args
            gr=self.canvas.graph
            for n in gr.nodes:
                if n.ID==evt.args[0]:
                    self.center_on(gr.pos[n])
                    break
        if 'add' in evt.type and evt.data == self.canvas.active_graph:
            #print 'appear',id(evt), evt.data.name, evt,'\n'
            item=evt.item
            self.canvas.icon[item].set_anim('appear',len=500,easing='quad')

        if  'add' in evt.type or 'change' in evt.type and True in [x in evt.infos for x in ('logic','val')]:
            owner=evt.data.owner
            #print '===================', evt.type,evt.data.name, match.data.actorgraph[owner].name
            truthchange=[]
            item=evt.item
            for ac1,rest in match.data.actorsubgraphs.iteritems():
                for ac2, gph in rest.iteritems():
                    if ac1!= owner and ac2!=owner:
                        #not necessary to reevaluate in subgraphs unconcerned by this evt
                        continue
                    if ac1!=ac2 and gph.contains(item) and (item.type=='node' or
                             not False in [gph.contains(p) for p in item.parents]):
                        if self.truth_calc(item,gph):
                            truthchange.append(gph)
            sgph =match.data.actorgraph[owner]
            if not sgph.contains(item):
                sub=match.data.actorsubgraphs[owner][owner]
                #print 'not contained in actorgraph', evt.item, sgph.name
                if self.truth_calc(item,sgph,sub):
                    truthchange.append(sub)
                #print '======================='
            if truthchange:
                #print 'Truth changed', evt.item, [i.name for i in truthchange]
                #anim=lambda t=item:self.canvas.icon[t].set_anim('blink')
                #wrap=FuncWrapper(anim,type='visual_appear_{}'.format(item),source=evt,priority=1)
                #match.add_phase(wrap)
                pass

        if ('change' in evt.type and 'bias' in evt.infos  and not 'truth' in evt.infos
            and not (evt.source and 'updbias' in evt.source)
             or 'add' in evt.type and not evt.infos.get('bias',None) is None
              and  evt.infos.get('truth',None) is None
            ):
                #print '*** bias set=> truthcalc', evt.item, evt.data.name, evt.infos['bias']

                self.truth_calc(evt.item,evt.data)
        if ('change' in evt.type and 'truth' in evt.infos and not 'bias' in evt.infos
             and not (evt.source and 'truthcalc' in evt.source)
             or 'add' in evt.type and  not evt.infos.get('truth',None) is None
             and evt.infos.get('bias',None) is None
            ):
            #print '*** truth set=> biascalc', evt.item, evt.data.name, evt.infos['truth']

            #Any external change of truth values in an other-subgraph (e.g. in reaction events)
            #causes owner to reevaluate
            owner=evt.data.owner
            subs=match.data.actorsubgraphs
            for oact,sao in subs[owner].iteritems():
                if oact != owner and evt.data==sao and sao.contains(evt.item):
                    #print 'Update bias perception in',owner,'about',oact, evt.item,' due to', evt
                    self.update_bias(evt.item,subs[owner][owner],sao)


    def update_bias(self, item,graph=None,sao=None,tracklist=None):
        #update what Actor thinks of another's biases so that they are consistent
        #with what Actor knows of other's truth values.
        if tracklist is None:
            tracklist=[]
        elif item in tracklist:
            return
        #print 'updating bias', item
        match=self.parent.handler
        srceff=match.ruleset.link_effect_from_source
        tgteff=match.ruleset.link_effect_from_target
        if graph is None:
            graph=self.canvas.active_graph

        should_have_truth=match.ruleset.calc_truth(item,graph,sao,extrapolate=1,bias=0)
        truth=sao.get_info(item,'truth')
        bias=truth-should_have_truth
        prevbias=graph.get_info(item,'bias')
        #print 'truth of {} is {} should be {} hence bias {} (before, {})'.format(item,truth, should_have_truth,bias,prevbias)
        if prevbias!=bias:
            self.canvas.change_infos(item,bias=bias,graph=sao,invisible=True)
        tracklist.append(item)
        for l in graph.links.get(item,[]):
            logic=graph.get_info(l,'logic')
            if l.parents[0]==item:
                if srceff(truth,logic) or srceff(should_have_truth,logic):
                    self.update_bias(l.parents[1],graph,sao,tracklist)
            elif tgteff(truth,logic) or tgteff(should_have_truth,logic):
                self.update_bias(l.parents[0],graph,sao,tracklist)
        return


class FogOfWar(pg.sprite.DirtySprite):

    def __init__(self,parent):
        super(FogOfWar, self).__init__()
        self.parent=parent
        self.image=pgsurface.Surface(parent.canvas.rect.size,pg.SRCALPHA)
        self.image.fill(graphic_chart['fog_color'])
        self.image.set_alpha(graphic_chart['fog_alpha'])
        self.rect=self.image.get_rect()
        self.image.convert()
        self.update()

    def remove_circle(self,center,radius):
        self.image.fill(graphic_chart['fog_color'])
        alpha=graphic_chart['fog_alpha']
        steps=graphic_chart['fog_steps']
        for s in range(steps)[::-1]:
            color = graphic_chart['fog_color'][:-1]+ (int(alpha*s/float(steps)),)
            pg.draw.circle(self.image,color,[int(i) for i in center],int(radius+(s-steps)*2))
        #self.mask = pg.mask.from_threshold(self.image,graphic_chart['fog_color'],(100,100,100,255))
        self.update()

    def update(self):

        self.mask =pg.mask.from_surface(self.image)


    def event(self,event,*args,**kwargs):
        if event.type == pg.MOUSEBUTTONDOWN and self.mask.g:
            return True
        return False
