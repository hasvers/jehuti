# -*- coding: utf-8 -*-

from gv_globals import *
from gv_data import DataBit
DEBUG=0

class Signal(DataBit):
#
    def __init__(self,type,*args,**kwargs):
        self.source=kwargs.pop('source',None) #source is not that important if each handler has a list of events that it has responded to
        self.type=type
        self.inverse=kwargs.pop('inverse',None) # inverse type (undo for do, unselect for select)
        self.args=args
        self.kwargs=kwargs

    def __repr__(self):
        if self.source:
            test=self.source+': '
        else :
            test=''
        return test+ self.type+' '+str(self.args) +' '+str(self.kwargs)

class EventCommander(object):
    '''
    Public functions are:
        -do
        -undo
        -pass_event
    '''

    def __init__(self,user):
        self.data=EventGraph()
        self.user=user
        self.handle=None #component that is passed on to events
        self.moving=[] #events that are currently being processed
        self.destination={} #when receive an order for events in processing, just store the destination
        self.killed=[] #events that were interrupted by force

        self._paused=False
        self.stacked=[]#events stacked during last pause

    @property
    def paused(self):
        return self._paused
    @paused.setter
    def paused(self,val):
        self._paused=val
        if not val :
            self.run_stack()

    def set_handle(self,handle):
        self.handle=handle

    def pass_event(self,evt,caller=None,ephemeral=False,**kwargs):
        #ephemeral is useful to represent one-off signals such as hover affecting status bar

        args=kwargs.pop('args',())
        if not ephemeral and not evt in self.data.stack+self.data.undo_stack:
            self.data.add_event(evt,*args)

        if caller:
            reacted=[caller]
        else:
            reacted=[]

        cs=self.user.ui.components+(self.user.ui,)
        succ = {}
        for c in cs :
            for i in c.depend.nodes():
                succ.setdefault(i,[])
                succ[i]+=c.depend.successors(i)

        if succ:
            if 0 and not ephemeral:
                print '--',evt, evt.affects()+(caller,),set( [x for z in [succ[i]  if i in succ else [] for i in evt.affects()+(caller,)] for x in z ])
            for i in evt.affects()+(caller,)+tuple(kwargs.get('affects',() )):
                if not i in succ:
                    continue
                for j in succ[i]:
                    if not j in reacted :
                        j.react(evt)
                        reacted.append(j)
            if 0 and not ephemeral :
                print '__',evt,reacted

        #for c in evt.current_children():
            #self.pass_event(c,caller,True,**kwargs)
        return evt

    def do(self,evt,caller=None,state=None,**kwargs):
        #print 'do', evt.type,id(evt), evt.state,state,debug.caller_name()
        for w in self.data.undo_stack:
            self.destroy(w) #maybe risk if that event happens to be in data.stack too
        self.data.undo_stack[:]=[]
        return self.evt_do(evt,state,**kwargs)


    def undo(self,event=None,state=None,*args,**kwargs):
        stack=self.data.stack
        if not self.data.stack or (event and not event in stack):
            return False
        if not event :
            i=-1
            event=stack[-1]
            while not self.evt_undo(event,state,*args,**kwargs):
                print 'not undoable', event,event.state
                i-=1
                return False
                #try:
                    #event= stack[i]
                #except:
                    #return False
        else:
            self.evt_undo(event,state,*args,**kwargs)
        try:
            self.data.undo_stack.append(event)
            stack.remove(event)
        except:
            #If event has been destroyed upon undo, forget it
            pass


        return True

    def redo(self,event=None,*args,**kwargs):
        if not self.data.undo_stack:
            return False
        undo_stack=self.data.undo_stack
        if event and not event in undo_stack:
            return False
        if not event :
            i=-1
            event=undo_stack[-1]
            while not self.evt_do(event,None,*args,**kwargs):
                i-=1
                try:
                    event= undo_stack[i]
                except:
                    return False
        else :
            self.evt_do(event,None,*args,**kwargs)

        if event in self.data.undo_stack:
            undo_stack.remove(event)
        if not event in self.data.stack:
            self.data.stack.append(event)

        return True



    def destroy(self,evt):
        #Remove event and all bound and children
        self.data.destroy_event(evt)

    def move_event(self,evt,state=None):

        self.move_walker(w,state)
        if w in self.data.bound : #all bound walkers are moved too
            for w2,st in self.data.bound[w][state]:
                self.move_walker(w2,st)


    def evt_do(self,evt,state=None,*args,**kwargs): #Only forward
        '''Called by self.do, runs alon path forward to a given state,
        if specified, or goes to next state.'''
        #print '> evt_do', evt.type,id(evt),evt.state,state,debug.caller_name()
        if state!= None :
            if state != evt.state:
                #if 0 and not state in evt.states.successors( (evt.state) ):
                    #print evt.states.edges(), evt.states.successors( (evt.state) )
                    #print 'not a successor', evt.state, state, evt
                    #if state in evt.states.predecessors( (evt.state) ):
                        #print 'but a predecessor'
                        #return evt_undo(self,evt,state,args,kwargs)
                    #raise Exception('No path')

                path = nx.shortest_path(evt.states,evt.state,state)
                if path[1]==state:
                    return self.evt_goto(evt,path[1],*args,**kwargs)
                elif self.evt_goto(evt,path[1],*args,**kwargs):
                    #TODO : find the right branch
                    #print 'evt_do calling evt_do', id(evt),state,debug.caller_name()
                    return self.evt_do(evt,state,*args,**kwargs)
                else:
                    self.destination.setdefault(evt,[]).append((state,args,kwargs))
        else :
            if kwargs.get('time',None)!=None:
                state=evt.state_at_time(kwargs['time'],
                    pass_block=kwargs.get('pass_block',False))
                return self.go(evt,state,*args,**kwargs)
            else:
                state=evt.states.successors(evt.state)[0]

       # print '> evt_do suite', id(evt)
        return self.evt_goto(evt,state,*args,**kwargs)

    def evt_undo(self,evt,state=None,*args,**kwargs): #Only backward
        '''Sams as evt_do, only backward.'''
        if state!= None:
            if evt.state != state: #undo all intermediary stages recursively
                self.evt_goto( evt,evt.states.predecessors(evt.state)[0],*args,**kwargs )
                return self.evt_undo(evt,state,*args,**kwargs)
        else :
            state = evt.state
        try:
            prec = evt.states.predecessors(state).pop()
        except:
            print 'Cannot undo', evt
            return False

        return self.evt_goto(evt,prec,*args,**kwargs)

    def go(self,evt,state,*args,**kwargs): #Like evt_do but both directions

        if evt.state==state and not evt.repeatable:
            return False
        #print '--go', evt.type,id(evt),evt.state,state,debug.caller_name()
        edge=(evt.state,state)
        redge=(state,evt.state)
        edges=evt.states.edges()
        if edge in edges or redge in edges:
            return self.evt_goto(evt,state,*args,**kwargs)
        if evt.state==state:
            path=[state]
        else:
            try:
                path = nx.shortest_path(evt.states,evt.state,state)
            except:
                path= nx.shortest_path(evt.states,state,evt.state)[::-1]
            if not evt.repeatable and path[0]==evt.state:
                path=path[1:]
        for i in path:
            if not self.evt_goto(evt,i,*args,**kwargs):
                return False
        return True

    def run_stack(self):
        '''Run all events stacked while commander was paused.'''
        #print 'Running stack', self.stacked
        [self.evt_goto(e,s,*a,**k) for e,s,a,k in self.stacked]
        self.stacked[:]=[]

    def evt_goto(self,evt,state,*args,**kwargs):
        '''Core function, never to be called directly, that runs events,
        changes their state, calls their children and bound events.'''

        if self.paused and not evt in self.moving and not (evt,state,args,kwargs) in self.stacked:
            self.stacked.append( (evt,state,args,kwargs))
            return False
        if evt.state==state and not evt.repeatable:
            #print '----- discontinued',id(evt)
            return False
        if evt in self.killed:
            return False
        if kwargs.get('override',False):
            if evt in self.moving:
                self.moving.remove(evt)
            if evt in self.destination:
                del self.destination[evt]
            for s in self.stacked:
                if s[0]==evt:
                    self.stacked.remove(s)
            self.killed.append(evt)
        elif evt in self.moving:
            dest= self.destination.setdefault(evt,[])
            if not (state,args,kwargs) in dest:
                dest.append((state,args,kwargs))
            #print '[[ On hold:', evt,state
            return False
        self.moving.append(evt)
        t,oldstate=time.time(),evt.state
        edge=(evt.state,state)
        #run all preparatory tasks like creating children or recovering previous states
        handle=kwargs.get('handle',self.handle)
        if handle:
            evt.prepare(edge,handle,*args,**kwargs)
        else :
            evt.prepare(edge,*args,**kwargs)
        handled=False
        priority=[ (0,evt) ]
        #print '   evt_goto', evt.type,id(evt),evt.state,state,debug.caller_name(),evt.states.node[state]['children_states']
        for c,s in evt.states.node[state]['children_states'].iteritems():
            if c in evt.states.node[state]['priority']:
                priority.append((evt.states.node[state]['priority'][c], c) )
            else :
                priority.append( (0,c) )

        priority=sorted(priority,key = lambda e: e[0], reverse=True )
        #if 'cflag' in evt.type:
            #print '\nPRIO',state, evt,id(evt),priority
        for p,c in priority:
            if c != evt :
                s = evt.states.node[state]['children_states'][c]
                #arg,kwarg=deepcopy(args),deepcopy(kwargs)
                arg=args[:]
                kwarg={}
                kwarg.update(kwargs)
                kwarg.pop('handle',None)
                kwarg=shallow_nested(kwarg)
                kwarg['ephemeral']=1
                kwarg['handle']=handle
                kwarg['traceback']=kwargs.get('traceback',[])[:]+[(evt,evt.state,p)]
                try:
                    arg=evt.states.node[state]['children_arg'][c]
                    kwarg=evt.states.node[state]['children_kwarg'][c]
                except:
                    pass

                chandled = self.go(c,s,*arg,**kwarg)
                handled=chandled or handled
                #if  'cflag' in evt.type:
                    #print '\n',evt, id(evt),c,id(c),'=====>',state,chandled
            else :
                if evt.state==state and not evt.repeatable:
                    continue
                kwarg={}
                kwarg.update(kwargs)
                handle=kwarg.pop('handle',self.handle)
                if handle:
                    evtdone =  evt.run(state,handle,*args,**kwarg)
                else :
                    evtdone =  evt.run(state,*args,**kwarg)

                if evtdone:
                    evt.state=state
                    self.pass_event(evt,None,kwargs.get('ephemeral',False) )
                    if (evt,state) in self.data.calls.nodes() : #bound events
                        #print 'yay',(evt,state),self.data.calls.succ[(evt,state)]
                        for e2,s2 in self.data.calls.neighbors( (evt,state) ):
                            if e2.state != s2:
                                self.go(e2,s2,**kwargs)
                handled = evtdone or handled
                #else:
                    #print 'FAIL', evt, state
        if evt.cues.get(state,None)=='destroy':
            self.destroy(evt)
        self.moving.remove(evt)
        t=time.time()-t
        if t>0.001 and DEBUG:
            import textwrap
            prel= len(self.moving)*'   ' + '|'
            txt= '\033[93m=== Event exec time {} (state {}->{}) === \033[0m'.format(t,oldstate,state)
            wrapper=textwrap.TextWrapper(initial_indent=prel,subsequent_indent=prel,width=90,break_long_words=False,replace_whitespace=False)
            print wrapper.fill(txt)
            for l in wrapper.wrap(str(evt)):
                print 'evtdebug',l

        if evt in self.destination:
            dest= self.destination[evt][:]
            while dest:
                d=dest.pop(0)
                if d[0]==evt.state:
                    continue
                #print ']] Releasing hold',evt,dest[0], 'after',state
                self.go(evt,d[0],*d[1],**d[2])
            try:
                del self.destination[evt]
            except:
                pass

        if kwargs.get('override',False):
            #print 'OVERR',evt, state,'\n', kwargs.get('traceback',[]),'\n\n',
            self.killed.remove(evt)
        else:
            pass
            #if hasattr(evt,'effects'):
                #print 'normal',evt, state, [(e,c,c.state) for e in evt.effects
                    #for c in e.all_children()],handled
        try:
            self.stacked.remove((evt,state,args,kwargs))
        except:
            pass
        return handled

    @property
    def stack(self):
        return self.data.stack

    @property
    def undo_stack(self):
        return self.data.undo_stack

class EventGraph(object):
    #Contains two types of links: paths and calls
    #Calls typically connect (states of) events to  (states of) their children
    #Paths typically connect two states of the same event

    def __init__(self):
        self.version=0
        self.stack=[]
        self.undo_stack=[]
        self.paths=nx.DiGraph()
        self.calls=nx.DiGraph()

        self.bound={}

    def add_event(self,evt,**kwargs):
        p=self.paths
        c=self.calls
        for state in evt.states:
            p.add_node((evt,state))
            c.add_node((evt,state))
        self.stack.append(evt)

    def rem_event(self,evt):
        for g in (self.paths,self.calls):
            for n in g.nodes():
                if n[0]==evt:
                    g.remove_node(n)
        try:
            self.stack.remove(evt)
        except:
            pass
        try:
            self.undo_stack.remove(evt)
        except:
            pass


    def destroy_event(self,evt):
        #remove event AND all bound events
        for g in (self.paths,self.calls):
            for n in g.nodes():
                if n[0]==evt:
                    for n2 in g.neighbors(n):
                        if n2[0]!=evt:
                            self.rem_event(n2[0])
                    g.remove_node(n)
        try:
            self.stack.remove(evt)
        except:
            try:
                self.undo_stack.remove(evt)
            except:
                pass

    def unbind(self,events,statecorr=None):
        self.bind(events,statecorr,True)

    def bind(self,events,statecorr=None,undo=False):
        for e in events:
            if not (e, e.state) in self.calls and not undo :
                self.add_event(e)
            for e2 in events :
                if e2!=e:
                    if not statecorr :
                        for s in e.states:
                            if s in e2.states:
                                #print 'Bind', (e.type,id(e),s),(e2.type,id(e2),s)
                                if not undo:
                                    self.calls.add_edge((e,s),(e2,s) )
                                else :
                                    try:
                                        self.calls.remove_edge((e,s),(e2,s) )
                                    except:
                                        pass
                    else:
                        for s,s2 in statecorr.get( (e,e2), []):
                            if not undo:
                                self.calls.add_edge((e,s),(e2,s2) )
                            else:
                                try:
                                    self.calls.remove_edge((e,s),(e2,s2) )
                                except:
                                    pass

    def old_bind_event(self,nevt,oevt,statecorresp):
        #never used yet
        if not nevt in self.walkers:
            self.add_event(nevt)
        ow =self.walkers[oevt]
        nw= self.walkers[nevt]
        for w in (nw,ow):
            if not w in self.bound:
                self.bound[w]={}
        for i, j in statecorresp:
            self.bound[nw].setdefault(i,[])
            self.bound[nw][i].append((ow,j))
            self.bound[ow].setdefault(j,[])
            self.bound[ow][j].append((nw,i))



    def next_version(self):
        self.version+=1

class DependencyGraph(nx.DiGraph):
    #Allows components to dynamically react to changes in data, whatever the source
    #by keeping track of what depends on which piece of data

    def __init__(self,*args,**kwargs):
        nx.DiGraph.__init__(self)
        self.parent=kwargs.get('parent',None)
        self.children=kwargs.get('children',[])

    def add_dep(self,x,y): #x depends on y
        self.add_edge(y,x)

    def rem_dep(self,x,y=None): #x depends on y
        if not y is None:
            try:
                self.remove_edge(y,x)
            except:
                pass
        else:
            try:
                self.remove_node(x)
            except:
                pass

class Event(Signal):

    parent=None
    repeatable=False #accepts "movements" from one state to the same
    desc='Event' #for any event list
    timed=False #flag to distinguished timed events (subclass)

    allow_duplicates=False #Does this event accept duplicate children?
            #Useful in case of successive do/undo

    def __init__(self,*args,**kwargs):
        self.parent=None # optional parent event
        self.state=0
        #self.children={} #indexed by state
        for i in kwargs.keys() :
            if i == 'parent' :
                self.parent = kwargs.pop(i)
            if i == 'desc' :
                self.desc = kwargs.pop(i)
            #if i == 'children' :
            #    self.children = kwargs.pop(i)
            #    for c in self.children:
            #        c.parent=self
            if i == 'repeatable':
                self.repeatable=j
        self._affects=kwargs.pop('affects',() )
        if not hasattr(self._affects,'__iter__'):
            self._affects=(self._affects,)
        else :
            self._affects=tuple(self._affects)
        Signal.__init__(self,kwargs.pop('type','event'),*args,**kwargs)
        self.cues={}

        self.states=nx.DiGraph()
        for n in (0,1):
            self.add_state(n)
        #self.states.add_edges_from(( (0,1), (1,0) ))
        self.states.add_edge( 0,1 )


    def __repr__(self):
        return self.type+' '+self.desc+' '+str(self.args)# +' '+str(self.kwargs)

    def affects(self):
        #list all the entities affected by this event
        return self._affects


    def current_children(self,recursive=False):
        if not recursive:
            return self.states.node[self.state]['children_states'].keys()
        else :
            children= set(self.states.node[self.state]['children_states'].keys())
            for c in tuple(children):
                children|=set(c.current_children(1))
            return children


    def clear_children(self):
        for state in self.states:
            children=self.states.node[state]['children_states'].keys()
            for c in children:
                del self.states.node[state]['children_states'][c]
                for t in ('priority','children_arg','children_kwarg'):
                    try:
                        del self.states.node[state][t][c]
                    except:
                        pass
                if c.parent==self:
                    c.parent=None


    def all_children(self,recursive=False):
        children=set([])
        for state in self.states:
            children|=set(self.states.node[state]['children_states'].keys())
        if recursive:
            children=set(children)
            for c in tuple(children):
                children|=set(c.all_children(1))
        return children

    def add_state(self,state,**kwargs ):
        self.states.add_node(state)
        self.states.node[state]['children_states']={}
        self.states.node[state]['priority']={}
        pred,suc=kwargs.get('pred',None),kwargs.get('suc',None)
        if pred!=None:
            self.states.add_edge(pred,state)
        if suc!=None:
            self.states.add_edge(state,suc)

    def duplicate_of(self,evt):
        if self==evt:
            return True
        return False

    #def copy(self):
        #return None
        #for n,d in j.nodes_iter(data=True):
            #new.__dict__[i].add_node(shallow_nested(n,make_new,**kwargs),
                #attr_dict=shallow_nested(d,make_new,**kwargs))
        #for e1,e2,d in j.edges_iter(data=True):
            #new.__dict__[i].add_edge(*tuple(
                #shallow_nested(x,make_new,**kwargs) for x in (e1,e2,d)))

    def check_duplicate(self,state,child,**kwargs):
        if not kwargs.get('duplicate_child',self.allow_duplicates):
            dupl=False
            for c in self.states.node[state]['children_states']:
                if c.duplicate_of(child):
                    dupl=True
            return dupl
        return False

    def add_child(self,child,statedict,*args,**kwargs):
        prior=kwargs.get('priority',False)
        for state in self.states.nodes():
            if self.check_duplicate(state,child,**kwargs):
                continue
            self.states.node[state]['children_states'][child]=statedict.get(state,0)
            if prior:
                self.states.node[state]['priority'][child]=prior

    def add_sim_child(self,child,**kwargs):
        #adds a child which follows exactly the same states as the parent
        prior=kwargs.get('priority',False)
        for state in self.states.nodes():
            if not state in child.states.nodes():
                continue
            if self.check_duplicate(state,child,**kwargs):
                continue
            self.states.node[state]['children_states'][child]=state
            if prior:
                self.states.node[state]['priority'][child]=prior
        if child.parent is None:
            child.parent=self

    def rem_child(self,child):
        for state in self.states.nodes():
            if child in self.states.node[state]['children_states']:
                del self.states.node[state]['children_states'][child]
                for t in ('priority','children_arg','children_kwarg'):
                    try:
                        del self.states.node[state][t][child]
                    except:
                        pass
        if child.parent==self:
            child.parent=None

    def prepare(self,*args,**kwargs):
        return False

    def run(self,*args,**kwargs):
        return True


class ChangeInfosEvt(Event):
    desc='Change infos'
    repeatable=True #Allows to apply it multiple times with different contents
    # states : 0 = no change/back to inital state. 1 = final state.

    def __init__(self,item,data,**kwargs):
        self.additive=kwargs.pop('additive',False)#For additive change of numeric informations

        #write attributes on item directly (instead of infos in a datastructure)
        #used for simple items that cannot belong to multiple datastructures (e.g. scripts)
        self.itemwrite=kwargs.pop('itemwrite',False)

        #data is the data container, kwargs are the infos (and some signal-related metainfos)
        super(ChangeInfosEvt, self).__init__(type='change_infos',**kwargs)
        self.data=data
        self.item=item
        self.oldinfo={}


    def __repr__(self):
        return '{} {} {} {}'.format(self.desc,self.data,self.item,self.kwargs)

    @property
    def infos(self):
        return self.sinfos(self.state)

    def duplicate_of(self,evt):
        if self.type==evt.type and self.item==evt.item and self.data==evt.data:
            if self.kwargs==evt.kwargs:
                return True
        return False

    def sinfos(self,state):
        if state==1:
            if not self.additive:
                return self.kwargs
            else :
                infos={}
                for i,j in self.kwargs.iteritems():
                    if hasattr(j,'keys'):
                        infos[i]={ z:k+self.oldinfo[i][z] for z,k in j.iteritems() }
                    else :
                        infos[i]=j+self.oldinfo[i]
                return infos
        if state==0:
            return self.oldinfo

    def affects(self):
        if hasattr(self.data,'precursors'):
            prec=self.data.precursors
        else:
            prec=()
        return (self.item,self.data)+prec


    def prepare(self,edge,*args,**kwargs):
        if edge == (0,1):
            if self.itemwrite:
                old={}
                for i in sorted(self.item.dft):
                    old[i]=getattr(self.item,i)
            else:
                old=self.data.get_info(self.item)
            self.oldinfo={}
            for i,j in old.iteritems():
                if i in self.kwargs:
                    self.oldinfo[i]= shallow_nested(j)


    def run(self,state,*args,**kwargs):
        #print '\nCHANGEINFOS',state,self,kwargs.get('traceback','No traceback')
        return self.apply_infos(self.sinfos(state))#either new or old depending on state

    def update(self,**kwargs):
        handled=False
        self.kwargs.update(kwargs)
        if self.state==1:
            handled= self.apply_infos(kwargs)
        return handled

    def apply_infos(self,infos):
        handled=False
        upd=self.kwargs.get('update',True)
        item=self.item
        if not self.itemwrite and not self.data.contains(item):
            print 'ChangeInfos on item that is not in data!',infos,  item, self.data
            return False
        for i,j in infos.iteritems():
            if self.itemwrite:
                if not hasattr(item,i):
                    continue
                if (not hasattr(getattr(item,i),'keys')) or not upd:
                    try:
                        item.set_attr(i,j) #better when item has its own method
                    except:
                        setattr(item,i,j)
                else:
                    getattr(item,i).update(j)
                handled=True
                if self.data and i in self.data.get_info(item,transparent=False):
                    #rare case when I want to update both
                    self.data.set_info(item,i,j,update=upd)
            elif self.data.set_info(item,i,j,update=upd):
                handled = True
        return handled

class AddEvt(Event):
    desc='Add'
    def __init__(self,item,data,**kwargs):
        self.inverted=kwargs.pop('inverted',False)
        if self.inverted :
            lab = 'rem_'
            self.desc= 'Remove'
        else :
            lab='add_'
        self.desc += ' '+item.type
        self.infos=kwargs.pop('infos',{} )
        super(AddEvt, self).__init__(type=lab+item.type,**kwargs)

        self.kwargs.setdefault("assess",True)
        self.kwargs.setdefault("update",True)
        self.item=item
        self.data=data
        #self.cues={'remove':0}
        self.temp=[] #children that must be removed after each undo/redo cycle
        if self.inverted:
            self.state=1
            self.states.add_edge( 1,0 )
            self.states.remove_edge( 0,1 )

    def __repr__(self):
        return '{} {} {} {}'.format(self.desc,self.item,self.data, self.state)

    def duplicate_of(self,evt):
        if self.type==evt.type and self.item==evt.item and self.data==evt.data:
            return True
        return False

    def affects(self):
        return (self.item,self.data)

    def prepare(self,edge,*args,**kwargs):
        if edge == (0,1):
            if self.kwargs.get('addrequired',False):
                for i in self.item.required:
                    if not i in self.data.infos and not i in self.states.node[1]['children_states'] :
                        evt = AddEvt(i,self.data, inverted=self.inverted,**self.kwargs)
                        self.add_sim_child( evt )
                        #required are first to come, last to go
                        self.states.node[1]['priority'][evt]=1
                        self.states.node[0]['priority'][evt]=-1
            #TODO : kwargs can contain things useful for children, but also infos specific to parent
        if edge==(1,0) :
            #Remove

            for c in self.temp:#residues from previous undo/redo
                self.rem_child(c)

            for i in self.data.infos.keys():
                if self.item in i.required:
                    #remove (and re-add upon redo) all dependent items
                    infos =self.data.infos[i]
                    evt=AddEvt(i,self.data,infos=infos, inverted=self.inverted,**self.kwargs)
                    self.add_sim_child( evt)
                    self.temp.append(evt)
                    #requirers are last to come, first to go
                    self.states.node[1]['priority'][evt]=-1
                    self.states.node[0]['priority'][evt]=1

            if not self.infos:
                self.infos=self.data.infos[self.item]
            subs=False
            for c in self.data.children:
                if self.item in c.infos:
                    subs=True
                    infos=c.infos[self.item]
                    kwarg={}
                    kwarg.update(self.kwargs)
                    evt=AddEvt(self.item,c,infos=infos,inverted=self.inverted,**kwarg)
                    self.add_sim_child( evt)
                    self.temp.append(evt)
                    self.states.node[1]['priority'][evt]=-2
                    self.states.node[0]['priority'][evt]=2
            if subs:
                #Unnecessary to update canvas after each small change
                self.kwargs['update']=False

    def run(self,state,*args,**kwargs):
        item=self.item
        if state == 1:
            handled = self.data.add(item,rule=self.kwargs.get('rule','none'),**self.infos)
            if handled and 'pos' in self.kwargs:
                try:
                    self.data.pos[item]=self.kwargs['pos']
                except:
                    pass
            return handled
        if state== 0:
            #print 'ADDEVT',self,state,kwargs.get('traceback','No traceback' )
            handled= self.data.remove(item)
            return handled

class SelectEvt(Event):
    desc='Select'
    def __init__(self,*args,**kwargs):
        super(SelectEvt, self).__init__(type='select',*args,**kwargs)
        self.item = args[0]
        self.cues={0:'destroy'}

    def duplicate_of(self,evt):
        if self.type==evt.type and self.item==evt.item:
            return True
        return False

class MoveEvt(Event):
    desc='Move'
    def __init__(self,item,graph,pos,**kwargs):
        super(MoveEvt, self).__init__(type='move',**kwargs)
        self.item = item
        self.pos=pos
        self.graph=graph

    def duplicate_of(self,evt):
        if self.type==evt.type and self.item==evt.item:
            if self.pos==evt.pos and self.graph==evt.graph:
                return True
        return False

    def __repr__(self):
        return '{} {} {}'.format(self.desc,self.item,self.pos)

    def affects(self):
        return (self.item, self.graph)+tuple(self._affects)

    def prepare(self,edge,*args,**kwargs):
        if edge == (0,1):
            self.oldpos=self.graph.pos[self.item]

    def run(self,state,*args,**kwargs):
        item = self.item
        if state==1:
            if tuple(self.graph.pos[item])!=tuple(self.pos):
                self.graph.pos[item]=self.pos
                return True
        if state==0:
            if tuple(self.graph.pos[item])!=tuple(self.oldpos):
                self.graph.pos[item]=self.oldpos
                return True
        print 'MOVE FAIL', state,tuple(self.graph.pos[item]),tuple(self.pos)
        return False


class TimedEvent(Event):
    timed=True
    repeatable=1
    def prepare(self,edge,*args,**kwargs):
        if edge==(0,1):
            for s in self.states.node:
                self.states.node[s]['started']=None
                self.states.node[s].setdefault('duration',0.)
                self.states.node[s].setdefault('waiting',False)
        return True

    def run(self,state,*args,**kwargs):
        if state>0 and self.states.node[state]['started'] == None:
            self.states.node[state]['started']=kwargs.get('time',None)
        return Event.run(self,state,*args,**kwargs)

    def state_at_time(self,time,**kwargs):
        '''Find the state in which this timed event SHOULD be
        at a given time (or else the last state before).'''
        laststate=self.state
        curstart=self.states.node[self.state]['started']
        pass_block=kwargs.get('pass_block',False) #Do you ignore blocking states?
        if not curstart:
            curstart=0
        for s in self.states.node:
            state=self.states.node[s]
            if state['started']!=None:
                if 0<= time -state['started'] < state['duration']:
                    return s
                if time -state['started']>= state['duration']:
                    if not curstart or state['started']>curstart:
                        laststate=s
                        curstart=state['started']
        state=self.states.node[laststate]
        if state['started']!=None:
            lasttime=state['started']+state['duration']
            if state['waiting'] and not pass_block:
                return laststate
        else:
            lasttime=0
        suc=self.states.successors(laststate)[:]
        while suc:
            nxt=suc.pop(0)
            state=self.states.node[nxt]
            if state['started']==None:
                if time-lasttime<=state['duration'] or state['waiting'] and not pass_block:
                    return nxt
            suc+=self.states.successors(nxt)
            laststate=nxt
        try:
            return self.states.successors(laststate)[0]
        except:
            return laststate