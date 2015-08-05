# -*- coding: utf-8 -*-

from collections import MutableMapping
from itertools import imap as itertools_imap
from gv_globals import *
import weakref




class World(object):
    '''ECS-style World: Contains the list of trueIDs representing objects,
    dictionaries pointing to the truest object corresponding to a given trueID
    (i.e. the one given by the most authoritative source, typically its creator)
    and to all references to a given trueID in databases'''

    def __init__(self):
        self.instances={} #for each trueID, list of databases that refer to it
        self.object=weakref.WeakValueDictionary() #Python object corresponding to each trueID for targets of info
            #(must be uploaded to the world from individual database as they create objects)
        self.database=weakref.WeakValueDictionary() #Same thing with Data objects (containers of info)
        self.reference={} #Database that holds the reference data on one dataobject

    def add_instance(self,ID,data):
        self.database.setdefault(data.trueID,data)
        self.instances.setdefault(ID,set() ).add(data.trueID)

    def record(self,obj,ref=None,force=False):
        if not hasattr(obj,'trueID'):
            return
        if ref and (force or not obj.trueID in self.reference) :
            self.reference[obj.trueID]=ref.trueID
        if not force:
            self.object.setdefault(obj.trueID,obj)
        else:
            self.object[obj.trueID]=obj

    def add_database(self,db):
        self.database[db.trueID]=db

    def rem_database(self,db):
        if db.trueID in self.database:
            del self.database[db.trueID]

world=World()


class DataContainer(object):
    '''Base class for DataList, DataDict and variants
    Identifies objects by their trueID, and fetches them'''

    def conv_key(self,key):
        '''If the key is an object, record its trueID instead'''
        if hasattr(key,'trueID'):
            return key.trueID
        return key

    def inverse_conv_key(self,key):
        '''Inverse conversion: retrieve nearest object associated with trueID'''
        return self.database.get_object(key)

    @property
    def database(self):
        db=self._database
        if isinstance(db,basestring):
            return world.database[db]
        return db

class DataList(list,DataContainer):
    '''List form of the DataContainer'''

    def __init__(self,database,*args):
        list.__init__(self,*args)
        self._database=database #Parent

    def __getitem__(self,key):
        return self.inverse_conv_key(list.__getitem__(self,key))

    def __setitem__(self,key,val):
        val=self.conv_key(val)
        world.add_instance(val,self.database)
        return list.__setitem__(self,key,val)

    def __getslice__(self,*args):
        return map(self.inverse_conv_key,list.__getslice__(self,*args))

    def __setslice__(self,i,j,val):
        val=self.conv_key(val)
        world.add_instance(val,self.database)
        return list.__setslice__(self,key,val)

    def __contains__(self,key):
        key=self.conv_key(key)
        return list.__contains__(self,key)

    def __iter__(self):
        return itertools_imap(self.inverse_conv_key,list.__iter__(self))

    def __repr__(self):
        vals=[i for i in self]
        if vals:
            return "DataList({},{})".format(self.database,vals)
        else:
            return "DataList({})".format(self.database)


class DataDict(dict,DataContainer):
    '''Special class of dictionary
     E.g. dic[obj] fetches dic[obj.trueID].
    Possibility of setting a default value.
    If default==None, throws an error for missing keys like normal dict'''

    def __init__(self,database, default=None,update=None):
        dict.__init__(self)
        self._database=database #Parent
        self.default=default
        if update:
            self.update(dict(update))

    def __missing__(self, key):
        if self.default is None:
            exc= 'Missing key {} in {}'.format(key,self)
            raise KeyError(exc)
        return self.default

    def __getitem__(self,key):
        key=self.conv_key(key)
        return dict.__getitem__(self,key)

    def __setitem__(self,key,val):
        key=self.conv_key(key)
        world.add_instance(key,self.database)
        return dict.__setitem__(self,key,val)

    def __delitem__(self,key):
        key=self.conv_key(key)
        return dict.__delitem__(self,key)

    def __contains__(self,key):
        key=self.conv_key(key)
        return dict.__contains__(self,key)

    def keys(self):
        return [self.inverse_conv_key(k) for k in dict.keys(self) ]

    def iterkeys(self):
        return itertools_imap(self.inverse_conv_key,dict.iterkeys(self))

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

    def __repr__(self):
        vals=dict((i,j) for i,j in self.iteritems())
        if vals:
            return "DataDict({},update={})".format(self.database,vals)
        else:
            return "DataDict({})".format(self.database)

class DataMat(DataDict):
    '''Two-dimensional equivalent of DataDict'''

    def __init__(self, database,default=None,update=None):
        dict.__init__(self)
        self._database=database #Parent
        self.default=default
        self.dummy=DataDummy(default, self)
        if update:
            self.update(dict(update))

    def __missing__(self, key):
        if self.default is None:
            exc= 'Missing key {} in {}'.format(key,self)
            raise KeyError(exc)
        self.dummy.miskey=key
        return self.dummy

    def __repr__(self):
        vals=dict((i,j) for i,j in self.iteritems())
        rpr="DataMat({},default={}".format(self.database,self.default)
        if vals:
            return rpr+",update={})".format(self.database,vals)
        else:
            return rpr+')'
        return


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



class Data(object):
    #can contain only objects susceptible of pickling, ie  independent objects recoverable as such
    name='data'
    datatype='data'
    fakelists=()
    infotypes={} #defines BOTH the types of objects contained here and the types of infos stored about them
    rule = 'all' #rule limiting objects that may be added here
    transparent = False # Parent-including: If transparent, anyone who sees this datastructure also sees anything from the parent
    overwrite_item= False #All infos that may be are inserted into the item
    _precursors=() #precursors include parent and are conceptually like it but only serve as info source
    contexts=() #contexts are precursors that should not be saved (e.g. gamewide variables)
    immutable=0 #see DataBit


    def precursors(self,item=None,mode='r'):
        prec=self._precursors+self.contexts
        if not self.parent is None:
            prec= (self.parent,)+prec
        if item and item.trueID in self.infos and mode=='r':
            #Look if item has been imported from somewhere,
            #only if you are trying to READ its properties (not write)
            imported_from= self.infos[item.trueID].get('exporter',None)
            if imported_from in world.database:
                imported_from=world.database[imported_from]
                prec=(imported_from,) + prec
            #Reference database i.e. source of info where item was created
            #(last resort if info is found nowhere)
            #try:
                #ref=world.database[world.reference[item.trueID]]
                #if ref!=self:
                    #prec=prec+(ref,)
            #except:
                #pass
        return prec

    def get_object(self,ID):
        if not isinstance(ID,basestring):
            #Temporary objects e.g. LinkGrabber and DataDict used as normal dict
            return ID
        if ID in self.obj_by_ID:
            return self.obj_by_ID[ID]
        for p in self.precursors():
            o=p.get_object(ID)
            if not o is None:
                return o
        return world.object[ID]

    def __init__(self,**kwargs):
        self.trueID='#{}{}{}#'.format(self.__class__.__name__,id(self), int(time.time()*1000))
        world.add_database(self)
        self.infos={}
        self.obj_by_ID={}
        self.infotypes=deepcopy(self.infotypes)
        self.typID=dict((i,1) for i in self.infotypes.keys())
        self.parent=None
        self.children=[]
        self.new_items=[] #lets any handler know what has changed

        for i, j in kwargs.iteritems() :
            if i == 'rule':
                self.rule = j
            if i=='parent':
                self.parent=j
                self.parent.children.append(self)
            if i=='precursors':
                self._precursors=j
            if i=='contexts':
                self.contexts=j
            if i=='name':
                self.name=name

        if kwargs.get('maketypedlists',True): #default: create a list for every type of item
            for i in self.infotypes.keys():
                if not hasattr(self,i+'s'):
                    setattr(self,i+'s',[])

    def __getstate__(self):
        return {i:j for i,j in self.__dict__.iteritems() if not i=='contexts'}

    def filename(self):
        return self.name+database[self.datatype+'_ext']


    def save(self):
        self.txt_export(filename=self.name)
        return
        #Obsolete===========================================================
        genre=self.datatype
        print 'Saving {} as'.format(genre),self.name
        fpath=resource_path(self.name,filetype=genre)
        #try:
            #shutil.copy2(fpath,path+'archive/'+filename+'.arc')
        #except:
            #pass
        try:
            bpath=database['basepath']+'logs/buffer.tmp'
            buff=fopen(bpath,'wb')
            pickle.dump( self,buff)
            buff.close()
            #fout=fopen(fpath,'wb')
            #pickle.dump( data,fout  )
            #fout.close()
            shutil.copy2(bpath,fpath)
            os.remove(bpath)
        except TypeError as e:
            print 'ERROR: Save_to_file '.e, self, self.__dict__


    def kill(self,recursive=False):
        if self.parent:
            try:
                self.parent.children.remove(self)
            except:
                pass
        for c in self.children:
            if c.parent==self:
                c.parent=None
                if recursive:
                    c.kill(recursive)
        self.renew()

    def is_sole_source(self,info_type,item):
        '''Is this Data object the only source of a given type of infos
        (e.g. it has no precursor with the same role).'''
        if not info_type in self.infotypes[item.type]:
            return False
        if self.overwrite_item:
            if hasattr(item,info_type):
                return False
        else:
            for p in self.precursors(item):
                if info_type in p.get_infotypes(item.type):
                    return False
            return True

    def get_info(self,item,info_type=None,**kwargs):
        iid=item.trueID
        if self.transparent and kwargs.get('transparent',True):
            #If transparent, look up info in precursors i.e. more general databases

            if info_type == None :
                tmp = {}
                for p in self.precursors(item):
                    info= p.get_info(item,info_type)
                    if info:
                        tmp.update(info)
                tmp.update(self.infos.get(iid,{}))
                return tmp
            if iid in self.infos and info_type in self.infos[iid] :
                #print item,info_type, self.infos[iid][info_type]
                return self.infos[iid][info_type]
            else :
                for p in self.precursors(item):
                    info= p.get_info(item,info_type)
                    if info!=None:
                        return info
                return None

        if info_type != None and not info_type in self.infotypes[item.type]:
            return None
        if not iid in self.infos :
            if not info_type:
                return {}
            else :
                return None
        if not info_type in self.infos[iid] :
            if info_type == None :
                return self.infos[iid]
            return None
        return self.infos[iid][info_type]

    def rem_info(self,item,info_type,**kwargs):
        if item.trueID in self.infos:
            if info_type in self.infos[item.trueID]:
                del self.infos[item.trueID][info_type]

    def objects(self):
        return [world.object[iid] for iid in self.infos]


    def set_info(self,item,ityp,val,**kwargs):
        rec=kwargs.get('recursive',False)

        ##Crucial: replace mutable objects by  something containing only
        # their trueID when they are used as value
        if hasattr(val,'trueID') and not val.immutable:
            val=val.trueID#WeakDataRef(val.trueID)

        #print self, item, ityp, val, self.infotypes[item.type]
        if ityp in self.infotypes[item.type]:
            iid=item.trueID

            # transfer value to object itself
            if hasattr(item,ityp) and (self.overwrite_item or kwargs.get('overwrite_item',False)) :
                if (not hasattr(getattr(item,ityp),'keys')) or not  kwargs.get('update',False):
                    setattr(item,ityp,val)
                else:
                    getattr(item,ityp).update(val)


            if not iid in self.infos :
                self.infos[iid]={}
            infos=self.infos[iid]
            if ityp in infos and kwargs.get('update',False):
                if hasattr(infos[ityp],'update') :
                    infos[ityp].update(val)
                elif hasattr(infos[ityp],'__iter__') and not hasattr(self.infos[item][ityp],'__hash__'):
                    infos[ityp]+=val
                else:
                    infos[ityp]=val
            else :
                infos[ityp]=val
            if not rec:
                return True

        if self.transparent or rec:
            for p in self.precursors(item,mode='w'):
                info= p.set_info(item,ityp,val)
                if info:
                    return info
        return False


    def add_infotype(self,item_type,info_type):
        if not hasattr(info_type, '__iter__'):
            info_type= (info_type,)
        elif not isinstance(info_type,tuple):
            info_type = tuple(info_type)
        self.infotypes[item_type]+=info_type
        return True

    def get_infotypes(self,item_type,force_opaque=False):
        '''Allow to get the infotypes including those of precursors
        (unless not transparent, or force_opaque is used,
        in which case the only advantage is for overrides)'''
        if not self.transparent or force_opaque:
            return self.infotypes[item_type]
        else:
            types=list(self.infotypes[item_type])
            pos = 0
            for p in self.precursors():
                for t in p.infotypes[item_type]:
                    if not t in types :
                        types.insert(pos,t)
                    else:
                        pos = types.index(t)+1
                return types
        return []

    def add(self,item,**kwargs):
        #If the trueID does not already exist in World, add it
        if not kwargs.get('exporter',False):
            world.record(item,self) #Record self as reference
        else:
            if not 'exporter' in self.infotypes[item.type]:
                self.infotypes[item.type]+=('exporter',)
            world.record(item)

        ityp= item.type
        added=False
        if not item.trueID  in self.infos:
            if not ityp in self.infotypes.keys():
                return False
            if item.required and False in ( self.contains(p) for p in item.required):
                if kwargs.get('addrequired',False):
                    [self.add(x) for x in item.required]
                else:
                    return False

            if not ityp+'s' in self.fakelists and hasattr(self,ityp+'s'):
                lst=getattr(self,ityp+'s')
                if isinstance(lst,list):
                    if item in lst:
                        print 'ERROR DIAGNOSIS',item, self, ityp+'s', lst,self.objects()
                        raise Exception('Item in list but not in infos.')
                    lst.append(item)
                if hasattr(item, 'ID') and not item.ID is None:
                    for oth in lst:
                        if oth!=item and oth.ID==item.ID:
                            item.ID=max(item.ID, max(o.ID for o in lst )  +1 )
                            break
                    if self.typID[ityp]<=item.ID:
                        self.typID[ityp]=item.ID+1
                else:
                    item.ID=self.typID[ityp]
                    self.typID[ityp]+=1
            added=True
            self.infos[item.trueID]={}

            if not item in self.new_items:
                self.new_items.append(item)

            if 'exporter' in kwargs:
                self.set_info(item,'exporter',kwargs['exporter'])
                #Set exporter first to test if this is sole source

            baseinfos={}
            for i in self.infotypes[item.type]:
                if hasattr(item,i) and self.overwrite_item:
                    baseinfos[i]=getattr(item,i)
                elif self.is_sole_source(i,item) and i in item.default_infos:
                    baseinfos[i]= deepcopy(item.default_infos[i])

            if self.transparent: #do not cover parent's infos with default infos !
                for j in iterchain(p.get_infotypes(item.type,force_opaque=1)
                             for p in self.precursors(item) if p):
                    for typ in j:
                        try:
                            del baseinfos[typ]
                        except:
                            pass

            baseinfos.update(kwargs)
            for i, j in baseinfos.iteritems():
                if i in self.infotypes[item.type] :
                    self.set_info(item,i,j)

        #even if it is already in the infos, do not bail out, try adding to children
        rule = kwargs.pop('rule',None)
        for c in self.children :
            if c.should_contain(item,rule):
                c.add(item,**kwargs)
        return added


    def remove(self,item):
        try:
            try:
                getattr(self,item.type+'s').remove(item)
            except:
                pass
            del self.infos[item.trueID]
            try:
                self.new_items.remove(item)
            except:
                pass
            return True
        except :
            return False

    def import_from_parent(self,**kwargs):
        if not self.parent :
            return False
        return self.import_from(self.parent,**kwargs)

    def import_from(self,data,**kwargs):
        items=kwargs.pop('items',[])
        try :
            items.append(kwargs['item'])
        except :
            pass
        rule = kwargs.pop('rule',None)
        if not items :
            if not rule :
                rule = self.rule
            item=[]
            for i in self.infotypes.keys():
                try:
                    item+=getattr(data,i+'s')
                except:
                    pass
            items += [i for i in data.objects() if not i in items]
        moved=[]
        while items :
            i=items.pop(0)
            if i.required and not i in moved:
                items.append(i)
                moved.append(i)
                continue
            sc=self.should_contain(i,rule)
            if sc:
                opt={}
                if 'infos' in kwargs and i.trueID in kwargs['infos']:
                    opt.update(kwargs['infos'][i.trueID])
                if hasattr(sc,'keys'):
                    opt.update(sc)
                #print self, i, opt
                self.add(i,**opt)

    def should_contain(self,item,rule=None):
        if not item.type in self.infotypes.keys():
            return False
        if not rule :
            rule = self.rule
        if isinstance(rule,basestring):
            if rule=='none':
                return False
            if rule =='all':
                return True
            if rule =='random':
                return rnd.uniform(0.,1.)<.8
            for comp in ('<','>','=','!='):
                tup=rule.split(comp)
                if len(tup)>1:
                    return eval( unicode(self.get_info(item,tup[0])) + comp + tup[1])
            return False

        if isinstance(rule,list):
            test = False
            for i in rule :
                if self.should_contain(item,i):
                    test=True
            return test

        if isinstance(rule,tuple):
            if rule[0] == item.type :
                return rule[1](item)
            else :
                return False
        return rule(item)

    def contains(self,item):
        return item.trueID in self.infos
    def __contains__(self,item):
        return item.trueID in self.infos

    def renew(self,renewinfotypes=True):
        self.infos={}#DataDict(self)
        for i in self.infotypes:
            #empty typedlists
            try:
                if isinstance(getattr(self,i+'s'),list):
                    del getattr(self,i+'s')[:]
            except :
                pass

        if renewinfotypes:
            self.infotypes=deepcopy(self.__class__.infotypes)
        self.typID=dict((i,1) for i in self.infotypes.keys())
        self.children=[]
        self.new_items=[]

    def finexport(self,txtdic,typdic,filename):
        '''Utility function that finalizes the text export procedure:
Opens the file and writes the items to it. '''
        #End of the text export procedure
        filename=resource_path(filename,filetype=self.datatype)
        fd = fopen(filename, "w")
        #print typdic
        for typ,keys in typdic.iteritems():
            for key in sorted(keys):
                fd.write(unicode(txtdic[key])+u'\n')
        fd.close()

    def txt_extract(self,o,keydic,txtdic,typdic):
        '''Utility function for the text export procedure:
Recursively explores data and replaces any reference to a game object by their key.'''
        #Recursive exploration and annotation
        if hasattr(o,'txt_export'):
            #Data or Databit
            if not id(o) in keydic:
                o.txt_export(keydic,txtdic,typdic)
            return u'{}'.format(keydic[id(o)])
        else:
            #Other data structure, to be explored
            test=lambda e:self.txt_extract(e,keydic,txtdic,typdic)
            if hasattr(o,'keys'):
                if isinstance(o,DataDict):
                    o.update({test(x):test(y) for x,y in o.iteritems()}  )
                    return o
                return o.__class__( (  (test(x),test(y)) for x,y in o.iteritems() ) )
            elif hasattr(o,'__iter__'):
                if 'array' in o.__class__.__name__ :
                    #Solves problems with numpy arrays
                    if not o.shape:
                        print 'ERROR: 0D array',o
                        if o == array(None):
                            return None
                        return float(o)
                    return u'array([' + ','.join([unicode(test(x)) for x in o]) +'])'
                return o.__class__([test(x) for x in o])
            elif isinstance(o,basestring):
                return '"'+o+'"'
            else:
                return o

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        '''Export an object as text. Called recursively, passing down:
            keydic
            txtdic
            typdic
        Accepts as keyword arguments:
            init_param: names of attributes that are needed at initialization
            add_param: names of attributes that must be exported'''
        #Export as text
        init_param=kwargs.pop('init_param',[])
        add_param=set(kwargs.pop('add_param',[]))#receive from subclasses specific attributes to save
        add_param.update(set(['name','rule','parent','children','infotypes',
            'transparent','overwrite_item','_precursors','typID']))
        if keydic is None:
            starter=True
            keydic,txtdic,typdic={},{},{}
        else:
            starter=False
        if hasattr(self,'klass_name'):
            klassn=self.klass_name
        else:
            klassn=self.__class__.__name__
        if not id(self) in keydic:
            keydic[id(self)]=self.trueID
            typdic.setdefault(klassn,[]).append(keydic[id(self)])
        txt=u"{}\n ##class:{}\n ##initparam:{}\n".format(
            keydic[id(self)],klassn,init_param)
        test=lambda e:self.txt_extract(e,keydic,txtdic,typdic)
        #Store attributes of this object
        dic={}
        for i in add_param:
            j=getattr(self,i)
            dic[i]=j
        #Store infos on other objects
        dicinf={}
        for i in self.infos:
            dicinf[i]={}
            test(world.object[i])
            for j,k in self.infos[i].iteritems():
                if isinstance(k,ndarray):
                    k,k2=tuple(k),k
                else:
                    k2=k
                try:
                    z=getattr(i,j)
                    if isinstance(z,ndarray):
                        z=tuple(z)
                except:
                    pass
                if not hasattr(i,j) or k!=z:
                    dicinf[i][j]=k2
        label=[u'##attr',u'##infos'] #NB: the label #attr is essentially useless
        for d in (dic,dicinf):
            txt+=u'{}\n'.format(label.pop(0))
            for i in sorted(d):
                j=d[i]
                tmp=u'{}:{}\n'.format(test(i),test(j))
                txt+=tmp
        txt+=u'##\n'
        txtdic[keydic[id(self)]]=txt
        if starter:
            return self.finexport(txtdic,typdic,kwargs['filename'])
        else:
            return keydic,txtdic,typdic


    def testrev(self,o,itemdic,secondrun=False):
        if isinstance(o,basestring):
            o=o.strip()
        try:
            if o in itemdic:
                return itemdic[o]
        except:
            pass

        if not secondrun:
            #When everything is still in the form of strings
            if isinstance(o,basestring):
                if o[0]==o[-1]=='"':
                    return o[1:-1]
                o=eval(o)
        test=lambda e:self.testrev(e,itemdic,secondrun)
        if hasattr(o,'keys'):
            if isinstance(o,DataDict):
                o.update({test(x):test(y) for x,y in o.iteritems()}  )
                return o
            return o.__class__( (  (test(x),test(y)) for x,y in o.iteritems() ) )
        elif hasattr(o,'__iter__'):
            if 'array' in o.__class__.__name__:
                return array([test(x) for x in o])
            return o.__class__([test(x) for x in o])
        else:
            return o


    def txt_import(self,filename):
        '''Overwrite content of this object with information imported from filename,
        which should contain this object as #0#, then its dependents as #n#.'''
        world.rem_database(self) #remove this object's 'trueID from world
        #Prepare
        fd=fopen(filename,filetype=self.datatype)
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
                key,val=[self.testrev(x.strip(),items) for x in l.split(':',1)]
                chunk[key]=val

        candidates=[] #Candidates to be this object
        to_init_last=[] #Objects that refer to others and must thus be initialized after
        if hasattr(self,'klass_name'):
            klassn=self.klass_name
        else:
            klassn=self.__class__.__name__
        for i,klass in klasses.iteritems():

            if klass==klassn:
                candidates.append(i)
            else:
                args=initparams.get(i,[])
                #print i,klass, args#,attrs[i].keys(),infos.get(i,{}).keys(),'parents' in attrs[i],'\n'
                args=[attrs[i][x] for x in args ]
                if set([x for x in args if isinstance(x,basestring)])& set(items.keys()):
                    to_init_last.append(i)
                else:
                    items[i]=self.klassmake(klass,*args)
        if len(candidates)==0:
            raise Exception('No object of corresponding class in text data')
        elif len(candidates)==1:
            items[candidates.pop()]=self
        else:
            left=[]
            c =None
            while candidates:
                if c:
                    left.append(c)
                c = candidates.pop(0)
                if attrs.get('name',None) ==self.name:
                    left+=candidates
                    candidates[:]=[]
            items[c]=self
            for i in left:
                args=initparams.get(i,[])
                items[i]=self.klassmake(klass,*[attrs[x] for x in args ])
        while to_init_last:
            i=to_init_last.pop(0)
            klass=klasses[i]
            args=[attrs[i][x] for x in initparams[i] ]
            args=[items[x] if isinstance(x,basestring) and x in items else x for x in args]
            if set([x for x in args if isinstance(x,basestring)])& set(items.keys()):
                to_init_last.append(i)
            else:
                items[i]=self.klassmake(klass,*args)
        self.renew()
        #Attributes
        for i,j in attrs.iteritems():
            item=items[i]
            for k,v in j.iteritems():
                key,val=[self.testrev(x,items,1) for x in (k,v)]
                if key=='infotypes':
                    #Check whether infotypes have changed
                    old=getattr(item,key)
                    diff=[(k,set(val.get(k,()))^set(old.get(k,() ) )) for k in set(val)|set(old) ]
                    diff=[str('on {}: infotypes {}'.format(k[0],list(k[1]))) for k in diff if k[1]]
                    if diff:
                        print 'Change in TxtImport: ',item.__class__, ' ; '.join(diff)
                else:
                    setattr(item,key,val)
            item.trueID=i

        #Infos
        for i,j in infos.iteritems():
            item=items[i]
            for k,v in j.iteritems():
                key,val=[self.testrev(x,items,1) for x in (k,v)]
                added=item.add(key,addrequired=True, **val)
                if not added:
                    if key in item:
                        item.infos[key.trueID].update(val)
                        #for x,y in val.iteritems()
                            #item.set_info(key,x,y)
                    else:
                        print 'Not added:', item, key, val
                        raise Exception('Adding error')



        fd.close()
        world.add_database(self)
    #def context_trans(self,item,dic):
        ##translates objects between contexts
        #if not hasattr(item,'truename'):
            #return item
        #return dic.get( item.truename,None)


    def add_context(self,context):
        '''A context is an underlying infosource that can be accessed by transparency
        but should not be saved together with this data object (e.g. because
        it comes from the database of the entire game)
        '''
        self.contexts+= context,

    def rem_context(self,context):
        self.contexts=(c for c in self.contexts if c!=context)


class DataBit(object):
    '''Urstructure of DataItem, cannot be the subject of information in a datastructure
    (i.e. is a pure value, never used as reference)'''
    dft={}
    immutable=1
    #If I make a copy of some object with this DataBit as one of its fields,
    #create instead a copy of the DataBit (i.e. behaves like tuple rather than list)
    #Set to 1 only if this DataBit is #never# used as reference
    #(thus false for DataItems that are used as reference in Data)


    def __init__(self,**kwargs):
        self.trueID='#{}{}{}#'.format(self.__class__.__name__,id(self), int(time.time()*1000))
        if not hasattr(self,'type'):
            self.type='databit'
        self.default_infos={}
        for i, j in self.dft.iteritems():
            if i in kwargs :
                setattr(self,i,kwargs[i])
            else :
                if hasattr(j,'__iter__'):
                    j=shallow_nested(j)
                setattr(self,i,j)
            self.default_infos[i]=getattr(self,i)

    def equals(self,item):
        if self.__class__ == item.__class__ and self.type ==item.type:
            for d in self.dft:
                if self.dft!=item.dft:
                    return False
            return True
        return False

    def set_attr(self,i,j):
        #Useful if I want to override it (for instance have some change trigger another)
        setattr(self,i,j)

    def copy(self):
        new=self.__class__()
        for i in self.dft:
            j=getattr(self,i)
            if hasattr(j,'__iter__'):
                j=shallow_nested(j)
            setattr(new,i,j)
        return new

    def txt_export(self,keydic,txtdic,typdic,**kwargs):
        init_param=kwargs.pop('init_param',[])
        add_param=set(kwargs.pop('add_param',[]))
        add_param.update(set(['type']))
        #add_param.add('trueID')
        if hasattr(self,'klass_name'):
            klassn=self.klass_name
        else:
            klassn=self.__class__.__name__

        if not id(self) in keydic:
            keydic[id(self)]=self.trueID
            typdic.setdefault(klassn,[]).append(keydic[id(self)])
        txt=u"{}\n ##class:{}\n ##initparam:{}\n".format(
            keydic[id(self)],klassn,init_param)
        test=lambda e:Data().txt_extract(e,keydic,txtdic,typdic)
        for i in set(sorted(self.dft))|set(add_param):
            if not hasattr(self,i):
                print 'ERROR: {} has no attr {}'.format(self,i)
                continue
            tmp=u'{}:{}\n'.format(test(i),test(getattr(self,i)))
            txt+=tmp
        txt+=u'##\n'
        txtdic[keydic[id(self)]]=txt

    def txt_import(self):
        pass


class DataItem(DataBit):

    required=() #=This dataitem can exist in a data structure only if all the required items are already there
    ID=None #ID given to it by the data structure
    immutable=0
    def __init__(self,**kwargs):
        if not hasattr(self,'type'):
            self.type='dataitem'
        DataBit.__init__(self,**kwargs)

    def txt_export(self,keydic,txtdic,typdic,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']=set(kwargs['add_param'])
        kwargs['add_param'].update(set(['required','ID']))
        DataBit.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def __setattr__(self,name,value):
        dname=debug.caller_name()
        if not True in [x  in  dname for x in ('txt_import','set_info',str(self.__class__.__name__ ))]:
            print "DataItem: set_attr called by", dname, name, value
        return DataBit.__setattr__(self,name,value)