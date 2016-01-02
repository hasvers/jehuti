# -*- coding: utf-8 -*-

from collections import MutableMapping
from itertools import imap as itertools_imap
from gv_globals import *
from weakref import WeakValueDictionary




class World(object):
    '''ECS-style World: Contains the list of trueIDs representing objects,
    dictionaries allowing to retrive said objects,
    canon source corresponding to a given trueID
    and dependency graphs between objects
    '''


    def __init__(self):
        self.instances={} #for each trueID, list of databases that refer to it
        self.object={}#WeakValueDictionary() #Python object corresponding to each trueID for targets of info
            #(must be uploaded to the world from individual database as they create objects)
        self.database={}#WeakValueDictionary() #Same thing with Data objects (containers of info)
        self.canon_source={} #Database that holds the reference data on one dataobject
        self.future_data={} #Database that contains all objects that have not been created yet
        #self.references={}
        self.ref_graph=nx.DiGraph() #All the objects that refer to another object
        self.init_graph=nx.DiGraph()

        self.load_state={} #How far along the loading process a node is

        self.explore()

    def get_object(self,key):
        if key in self.object:
            return self.object[key]
        elif key in self.future_data:
            self.make_data(key)
            return self.object[key]
        elif isinstance(key,basestring) and key[0]==key[-1]=='#':
            raise KeyError("Missing object in world! {}".format(key))
        else:
            return key

    def add_instance(self,ID,data):
        self.database.setdefault(data.trueID,data)
        self.instances.setdefault(ID,set() ).add(data.trueID)

    def record(self,obj,ref=None,force=False):
        if not hasattr(obj,'trueID'):
            return
        if ref and (force or not obj.trueID in self.canon_source) :
            self.canon_source[obj.trueID]=ref.trueID
        if not force:
            self.object.setdefault(obj.trueID,obj)
            #print 'RECORDING',obj,obj.trueID, self.find(obj.trueID)
        else:
            self.object[obj.trueID]=obj
        self.load_state[obj.trueID]='loaded'

    def add_database(self,db):
        self.database[db.trueID]=db
        self.load_state[db.trueID]='loaded'

    def rem_database(self,db):
        if db.trueID in self.database:
            del self.database[db.trueID]

    def explore(self):
        '''Look recursively through the whole game folder to find all
game objects that it may have to create later.'''
        for term in database:
            if '_path' in term:
                path=database[term]
                filetype=term.replace('_path','')
                if filetype+'_ext' in database:
                    #Deduces that this is a proper datafile
                    for f in olistdir(filetype=filetype,with_path=True):
                        self.explore_file(f)
        #self.ref_graph=nx.DiGraph()
        #self.init_graph=nx.DiGraph()
        for itemID in self.future_data:
            dat=self.future_data[itemID]
            for dic in ('attr','info'):
                if dat[dic] is None:
                    continue
                for k,v in tuple(dat[dic].iteritems()):
                    for oID in self.future_data:
                        if oID in v:
                            ##self.references[oID].add(itemID)
                            self.ref_graph.add_edge(itemID,oID)
                            if k[1:-1] in dat['initparam']:
                                self.init_graph.add_edge(itemID,oID)
        self.priority={j:i for i,j in  enumerate(nx.topological_sort(self.init_graph)) }

    def explore_file(self,filename):
        fd=fopen(filename,'rb')
        attrs={}
        infos={}
        chunk={}
        items={}
        klasses={}
        initparams={}
        trueID={}
        lastid=None
        mode='attr'
        lines=[]
        for line in fd:
            l= line.strip()
            if len(l)>2 and l[0]==l[-1]=='#':
                items[l]=l
                klasses[l]=None
                attrs[l]={}
                infos[l]=None
                initparams[l]=[]
            lines.append(l)
        #Read lines
        for l in lines:
            #chunk = series of lines belonging to the same object
            if not l:
                continue
            if l=='##':
                if mode=='info':
                    infos[lastid]=chunk
                else:
                    attrs[lastid]=chunk
                chunk={}
                mode='attr'
            elif '##info' in l:
                attrs[lastid]=chunk
                #trueID[lastid]=chunk['trueID']
                chunk={}
                mode='info'
            elif 'class:' in l:
                klasses[lastid]=l.split(':',1)[1].strip()
            elif '##initparam' in l:
                initparams[lastid]=eval(l.split(':',1)[1].strip())
            elif len(l)>1 and l[0]==l[-1]=='#' :
                lastid=l
            elif l[:2]!='##':
                key,val=[x.strip() for x in l.split(':',1)]
                chunk[key]=val
        fd.close()
        for item in items:
            self.future_data[item]={'klass':klasses[item],'attr':attrs[item],
                'info':infos[item],'initparam':initparams[item]}
            self.init_graph.add_node(item)
            self.ref_graph.add_node(item)
        return items


    def import_analyze(self,o,itemdic,priority=0,mode=None):
        if isinstance(o,basestring) and o in itemdic:
            if not itemdic[o]==o:
                return itemdic[o]
        #if isinstance(o,basestring):
            #o=o.strip()
            #if o in itemdic and self.load_state.get(o,None)!='loaded':
                #if mode =='start':
                    #return self.start_make(o)
                #if mode=='end' and o in self.treating:
                    #self.treating.remove(o)
                    #return self.end_make(o)
                #if mode=='make':
                    #return self.make_data(o)
            #elif o in itemdic:
                #return itemdic[o]

        if not mode:# not secondrun:
            #When everything is still in the form of strings
            if isinstance(o,basestring):
                if o[0]==o[-1]=='"':
                    o=o[1:-1]
                    return o
                if not o[0]==o[-1]=='#':
                    try:
                        o=eval(o)
                    except Exception as e:
                        print 'Exception', e,o
                        return o

        test=lambda e:self.import_analyze(e,itemdic,priority,mode)
        if hasattr(o,'keys'):
            o= DataDict( (  (test(x),test(y)) for x,y in o.iteritems() ) )
            return o
        elif hasattr(o,'__iter__'):
            lst=[test(x) for x in o]
            if 'array' in o.__class__.__name__:
                return array(lst)
            #if isinstance(o,list):
                #return DataList([test(x) for x in o])
            return o.__class__(lst)
        else:
            return o

    def find(self,ID):
        if ID in self.object:
            return self.object[ID]
        elif ID in self.database:
            return self.database[ID]
        elif ID in self.load_state:
            #print ID, self.load_state[ID], self.database.get(ID,None),self.object.get(ID,None)
            raise Exception("WORLD: COULD NOT FIND", ID)
        return ID

    def make_data(self,itemID):
        started=[]
        if not isinstance(itemID,basestring):
            itemID=itemID.trueID
        if not itemID in self.future_data:
            raise Exception( 'Not in future_data {}'.format(itemID))

        #print 'Making',itemID
        if itemID in self.load_state:
            item=self.find(itemID)
        else:
            for oID in self.init_graph.neighbors(itemID):
                if  not oID in self.load_state:
                    other=self.start_make(oID)
                    started.append(other)
            item=self.start_make(itemID)
        if self.load_state[itemID]=='started':
            for oID in self.ref_graph.neighbors(itemID):
                if not oID in self.load_state:
                    other=self.make_data(oID)
                elif self.load_state[oID]=='started':
                    started.append(self.find(oID))
            self.end_make(itemID)
            for other in started:
                    self.make_data(other.trueID)
        return item


    def start_make(self,itemID):
        '''Creates the item, requiring only previous initialization of the initparam
        (which cannot be looped), so that item can be inserted into attributes/infos
        in other items even if there are loops.'''
        if not itemID in self.future_data:
            return itemID
        if itemID in self.object:
            return self.object[itemID]
        elif itemID in self.database:
            return self.database[itemID]

        chunk=self.future_data[itemID]
        info,attr={},{}
        if chunk['info']:
            info.update(chunk['info'])
        attr.update(chunk['attr'])

        klass=chunk['klass']
        if not chunk['info'] is None:
            mode='database'
        else:
            mode='dataitem'

        items=dict([(i,self.find(i) ) for i in self.future_data ])
        args=[attr['"{}"'.format(x)]  for x in chunk['initparam']]
        args=[self.import_analyze(x,items) for x in args ]
        item=self.klassmake(self,klass,*args)
        item.trueID=itemID

        if mode=='database':
            self.add_database(item)
        else:
            self.record(item)
        self.load_state[itemID]='started'
        return item

    def end_make(self,itemID):
        if self.load_state[itemID]!='started':
            return self.find(itemID)
        #print 'ENDING',itemID,self.load_state[itemID]
        chunk=self.future_data[itemID]
        if itemID in self.object:
            item=self.object[itemID]
        else:
            item=self.database[itemID]
        info,attr={},{}
        if chunk['info']:
            info.update(chunk['info'])
        attr.update(chunk['attr'])
        items=dict([(i,self.find(i) )  for i in self.future_data])
        #args=[attr['"{}"'.format(x)]for x in chunk['initparam']]
        #args=[self.import_analyze(x,items,mode='end') for x in args ]


        #Set attributes
        for k,v in attr.iteritems():
            if k=='trueID':
                continue
            key,val=[self.import_analyze(x,items) for x in (k,v)]
            if key=='infotypes':
                #Check whether infotypes have changed
                old=getattr(item,key)
                diff=[(k,set(val.get(k,()))^set(old.get(k,() ) )) for k in set(val)|set(old) ]
                diff=[str('on {}: infotypes {}'.format(k[0],list(k[1]))) for k in diff if k[1]]
                if diff:
                    print 'Change in TxtImport: ',item.__class__, ' ; '.join(diff)
            else:
                setattr(item,key,val)

        #Infos
        for k,v in info.iteritems():
            key,val=[self.import_analyze(x,items) for x in (k,v)]
            if not hasattr(key,'trueID'):
                key=self.make_data(key)
            added=item.add(key,addrequired=True, **val)
            if not added:
                if key in item:
                    item.infos[key.trueID].update(val)
                    #for x,y in val.iteritems()
                        #item.set_info(key,x,y)
                else:
                    print 'Not added:', item, key, val
                    raise Exception('Adding error')
        #print '===== Finished',itemID

        #print '\n',args, [x in self.treating for x in args], [ items.get(x,None) for x in args],str(chunk['initparam']
        self.load_state[itemID]='loaded'
        return item

world=World()


class DataContainer(object):
    '''Base class for DataList, DataDict and variants
    Identifies objects by their trueID, and fetches them'''

    def conv_key(self,key):
        '''If the key is an object, record its trueID instead'''
        if hasattr(key,'trueID'):
            key= key.trueID
        elif not isinstance(key,basestring):
            print 'DATACONTAINER ERROR:',key
        return key

    def inverse_conv_key(self,key):
        '''Inverse conversion: retrieve nearest object associated with trueID'''
        #return self.database.get_object(key)
        if isinstance(key,basestring):
            find=world.find(key)
            if find==key and key in world.future_data:
                key =world.make_data(key)
            else:
                if find==key and key[0]==key[-1]=='#':
                    raise Exception("DID NOT FIND KEY",key)
                key=find
        return key

    #@property
    #def database(self):
        #db=self._database
        #if isinstance(db,basestring):
            #return world.database[db]
        #return db

class DataList(list,DataContainer):
    '''List form of the DataContainer'''

    def __init__(self,arg=None):
        if arg:
            arg=[self.conv_key(v) for v in arg]
            list.__init__(self,arg)
        else:
            list.__init__(self)

    def __getitem__(self,key):
        res=list.__getitem__(self,key)
        if isinstance(res,list):
            return map(self.inverse_conv_key,res)
        return self.inverse_conv_key(res)

    def pop(self,key):
        return self.inverse_conv_key(list.pop(self,key))

    def __setitem__(self,key,val):
        if hasattr(val,'__iter__'):
            val=[self.conv_key(i) for i in val]
        else:
            val=self.conv_key(val)
        #world.add_instance(val,self.database)
        return list.__setitem__(self,key,val)

    def __getslice__(self,*args):
        return map(self.inverse_conv_key,list.__getslice__(self,*args))

    def __setslice__(self,i,j,val):
        val=self.conv_key(val)
        #world.add_instance(val,self.database)
        return list.__setslice__(self,key,val)

    def __contains__(self,key):
        key=self.conv_key(key)
        return list.__contains__(self,key)

    def append(self,val):
        val=self.conv_key(val)
        return list.append(self,val)

    def index(self,val):
        val=self.conv_key(val)
        return list.index(self,val)

    def insert(self,pos,val):
        val=self.conv_key(val)
        return list.insert(self,pos,val)

    def remove(self,val):
        list.remove(self,self.conv_key(val))

    def __iter__(self):
        return itertools_imap(self.inverse_conv_key,list.__iter__(self))

    def __repr__(self):
        vals=[i for i in self]
        return str(vals)

    def __add__(self,l):
        return list.__add__([self.conv_key(i) for i in l])
        return str(vals)

    def __str__(self):
        return list.__str__(self)

class DataDict(dict,DataContainer):
    '''Special class of dictionary
     E.g. dic[obj] fetches dic[obj.trueID].
    Possibility of setting a default value.
    If default==None, throws an error for missing keys like normal dict'''
    default=None

    #def __init__(self,database, default=None,update=None):
    def __init__(self,*args):
        dict.__init__(self)
        #self._database=database #Parent
        #self.default=default
        if args:
            self.update(dict(args[0]))

    def __missing__(self, key):
        if self.default is None:
            exc= 'Missing key {} {} in {}'.format(key,world.get_object(key),self)
            raise KeyError(exc)
        return self.default

    def __getitem__(self,key):
        key=self.conv_key(key)
        return dict.__getitem__(self,key)

    def __setitem__(self,key,val):
        key=self.conv_key(key)
        #world.add_instance(key,self.database)
        return dict.__setitem__(self,key,val)

    def __delitem__(self,key):
        key=self.conv_key(key)
        return dict.__delitem__(self,key)

    def __contains__(self,key):
        if hasattr(key,'trueID'):
            key=self.conv_key(key)
        return dict.__contains__(self,key)

    def keys(self):
        return [self.inverse_conv_key(k) for k in dict.keys(self) ]

    def iterkeys(self):
        return itertools_imap(self.inverse_conv_key,dict.iterkeys(self))

    def iteritems(self):
        return ((self.inverse_conv_key(i),j) for i,j in dict.iteritems(self))

    def __iter__(self):
        return self.iterkeys()

    def get(self,key,other=None):
        if key in self:
            return self[key]
        else:
            return other

    def setdefault(self,key,dft):
        if key in self:
            return self[key]
        else:
            self[key]=dft
            return self[key]

    def update(self,dic):
        for i,j in dic.iteritems():
            self[i]=j

    def __repr__(self):
        vals=dict((i,j) for i,j in self.iteritems())
        return str( vals)
        #if vals:
            #return "DataDict({},update={})".format(self.database,vals)
        #else:
            #return "DataDict({})".format(self.database)

    def __str__(self):
        return dict.__str__(self)


class DataMat(DataDict):
    '''Two-dimensional equivalent of DataDict'''

    def __init__(self,dic=None,default=None):
        dict.__init__(self)
        #self._database=database #Parent
        self.default=default
        self.dummy=DataDummy(default, self)
        if dic:
            self.update(dict(dic))

    def __missing__(self, key):
        if self.default is None:
            exc= 'Missing key {} {} in {}'.format(key,world.get_object(key),self)
            raise KeyError(exc)
        self.dummy.miskey=key
        return self.dummy

    def __repr__(self):
        vals=dict((i,dict(j)) for i,j in self.iteritems())
        return str(vals)


class DataDummy(MutableMapping):
    '''Exists temporarily to create a new row in a DataMat'''
    def __init__(self, default=0, parent=None):
        self.default=default
        self.parent=parent
        self.miskey=None
    def __getitem__(self, key):
        return self.default
    def __setitem__(self, key, value):
        newrow=DataDict(self.parent.database,self.default)
        newrow[key] = value
        self.parent[self.miskey]=newrow
    def __delitem__(self, key):
        return False
    def __iter__(self):
        return iter([])
    def __len__(self):
        return 0


