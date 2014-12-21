# -*- coding: utf-8 -*-

from gv_globals import *

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
    nested_copy=0 #see DataBit

    @property
    def precursors(self):
        if not self.parent is None:
            return (self.parent,)+self._precursors+self.contexts
        else:
            return self._precursors+self.contexts

    def __init__(self,**kwargs):
        self.infos={}
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

        if kwargs.get('maketypedlists',True): #default: create a list for every type of item
            for i in self.infotypes.keys():
                if not hasattr(self,i+'s'):
                    setattr(self,i+'s',[])

    def __getstate__(self):
        return {i:j for i,j in self.__dict__.iteritems() if not i=='contexts'}

    def filename(self):
        return self.name+database[self.datatype+'_ext']

    def kill(self):
        if self.parent:
            try:
                self.parent.children.remove(self)
            except:
                pass
        for c in self.children:
            if c.parent==self: #should I kill them too?
                c.parent=None
        self.renew()

    def get_info(self,item,info_type=None,**kwargs):
        if self.transparent and kwargs.get('transparent',True):
            if info_type == None :
                tmp = {}
                for p in self.precursors:
                    tmp.update(p.get_info(item))
                tmp.update(self.infos.get(item,{}))
                return tmp
            try :
                #print item,info_type, self.infos[item][info_type]
                return self.infos[item][info_type]
            except :
                for p in self.precursors:
                    info= p.get_info(item,info_type)
                    if info!=False:
                        return info
                return False

        if info_type != None and not info_type in self.infotypes[item.type]:
            return False
        if not item in self.infos :
            if not info_type:
                return {}
            else :
                return False
        if not info_type in self.infos[item] :
            if info_type == None :
                return self.infos[item]
            return False
        return self.infos[item][info_type]

#           keep in mind: storing some info in the items themselves ?
#            try :
#                self.infos[item][info] = getattr(item,info)
#            except :


    def set_info(self,item,ityp,val,**kwargs):
        rec=kwargs.get('recursive',False)

        #print self, item, ityp, val, self.infotypes[item.type]
        if ityp in self.infotypes[item.type]:

            # transfer value to object itself
            if hasattr(item,ityp) and (self.overwrite_item or kwargs.get('overwrite_item',False)) :
                if (not hasattr(getattr(item,ityp),'keys')) or not  kwargs.get('update',False):
                    setattr(item,ityp,val)
                else:
                    getattr(item,ityp).update(val)


            if not item in self.infos :
                self.infos[item]={}
            if ityp in self.infos[item] and kwargs.get('update',False):
                if hasattr(self.infos[item][ityp],'update') :
                    self.infos[item][ityp].update(val)
                elif hasattr(self.infos[item][ityp],'__iter__') and not hasattr(self.infos[item][ityp],'__hash__'):
                    self.infos[item][ityp]+=val
                else:
                    self.infos[item][ityp]=val
            else :
                self.infos[item][ityp]=val
            if not rec:
                return True

        if self.transparent or rec:
            for p in self.precursors:
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

    def get_infotypes(self,item_type):
        if not self.transparent:
            return self.infotypes[item_type]
        else:
            types=list(self.infotypes[item_type])
            pos = 0
            for p in self.precursors:
                for t in p.infotypes[item_type]:
                    if not t in types :
                        types.insert(pos,t)
                    else:
                        pos = types.index(t)+1
                return types

    def add(self,item,**kwargs):
        ityp= item.type
        added=False
        if not item in self.infos:
            #even if it is already in the infos, do not bail out, try adding to children
            if not ityp in self.infotypes.keys():
                return False
            if item.required and False in (p in self.infos for p in item.required):
                if kwargs.get('addrequired',False):
                    [self.add(x) for x in item.required]
                else:
                    return False

            if not ityp+'s' in self.fakelists and hasattr(self,ityp+'s'):
                lst=getattr(self,ityp+'s')
                if isinstance(lst,list):
                    if item in lst:
                        print 'ERROR DIAGNOSIS',item, self, ityp+'s', lst,self.infos.keys()
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
            self.infos[item]={}

            if not item in self.new_items:
                self.new_items.append(item)

            baseinfos={}
            for i in self.infotypes[item.type]:
                if hasattr(item,i):
                    baseinfos[i]=getattr(item,i)
                elif i in item.default_infos:
                    baseinfos[i]= deepcopy(item.default_infos[i])

            if self.transparent: #do not cover parent's infos with default infos !
                for j in iterchain(p.infotypes[item.type] for p in self.precursors if p):
                    for typ in j:
                        try:
                            del baseinfos[typ]
                        except:
                            pass

            baseinfos.update(kwargs)
            for i, j in baseinfos.iteritems():
                if i in self.infotypes[item.type] :
                    self.set_info(item,i,j)

        rule = kwargs.pop('rule',None)
        for c in self.children :
            if c.should_contain(item,rule):
                c.add(item,**kwargs)
        return added


    def remove(self,item):
        try:
            del self.infos[item]
            try:
                self.new_items.remove(item)
            except:
                pass
            try:
                getattr(self,item.type+'s').remove(item)
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
            items += [i for i in data.infos.keys() if not i in items]
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
                if 'infos' in kwargs and i in kwargs['infos']:
                    opt.update(kwargs['infos'][i])
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
                    return eval( str(self.get_info(item,tup[0])) + comp + tup[1])
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
        return item in self.infos

    def renew(self,renewinfotypes=True):
        self.infos={}
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
        #End of the text export procedure
        filename=database.get(self.datatype+'_path', database['basepath']) +filename+'.arc.txt'
        fd = fopen(filename, "wb")
        #print typdic
        for typ,keys in typdic.iteritems():
            for key in sorted(keys):
                fd.write(txtdic[key]+'\n')
        fd.close()

    def testport(self,o,keydic,txtdic,typdic):
        #Recursive exploration and annotation
        if hasattr(o,'txt_export'):
            if not id(o) in keydic:
                o.txt_export(keydic,txtdic,typdic)
            return '#{}#'.format(keydic[id(o)])
        else:
            test=lambda e:self.testport(e,keydic,txtdic,typdic)
            if hasattr(o,'keys'):
                return o.__class__( (  (test(x),test(y)) for x,y in o.iteritems() ) )
            elif hasattr(o,'__iter__'):
                if 'array' in o.__class__.__name__ :
                    if not o.shape:
                        print 'ERROR: 0D array',o
                        if o == array(None):
                            return None
                        return float(o)
                    return 'array([' + ','.join([str(test(x)) for x in o]) +'])'
                return o.__class__([test(x) for x in o])
            elif isinstance(o,basestring):
                return '"'+o+'"'
            else:
                return o

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
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

            keydic[id(self)]=len(keydic.keys() )
            typdic.setdefault(klassn,[]).append(keydic[id(self)])
        txt="#{}#\n ##class:{}\n ##initparam:{}\n".format(
            keydic[id(self)],klassn,init_param)
        test=lambda e:self.testport(e,keydic,txtdic,typdic)
        dic={}
        for i in add_param:
            j=getattr(self,i)
            dic[i]=j
        dicinf={}
        for i in self.infos:
            dicinf[i]={}
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
        label=['##attr','##infos'] #NB: the label #attr is essentially useless
        for d in (dic,dicinf):
            txt+='{}\n'.format(label.pop(0))
            for i in sorted(d):
                j=d[i]
                tmp='{}:{}\n'.format(test(i),test(j))
                txt+=tmp
        txt+='##\n'
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
            return o.__class__( (  (test(x),test(y)) for x,y in o.iteritems() ) )
        elif hasattr(o,'__iter__'):
            if 'array' in o.__class__.__name__:
                return array([test(x) for x in o])
            return o.__class__([test(x) for x in o])
        else:
            return o

    def klassmake(self,klass,*args):
        #paste in subclasses to use the namespace of the file they live in
        #certainly a better way to do this
        return eval(klass)(*args)

    def txt_import(self,filename):
        try:
            fd=fopen(filename,'rb')
        except:
            filename=database.get(self.datatype+'_path', database['basepath']) +filename+'.arc.txt'
            fd = fopen(filename, "rb")
        attrs={}
        infos={}
        chunk={}
        items={}
        klasses={}
        initparams={}
        lastid=None
        mode='attr'
        lines=[]
        for line in fd:
            l= line.strip()
            if len(l)>2 and l[0]==l[-1]=='#':
                items[l]=l
            lines.append(l)
        for l in lines:
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

        candidates=[]
        to_init_last=[]
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
        for i,j in attrs.iteritems():
            item=items[i]
            for k,v in j.iteritems():
                key,val=[self.testrev(x,items,1) for x in (k,v)]
                if key=='infotypes':
                    old=getattr(item,key)
                    diff=[(k,set(val.get(k,()))^set(old.get(k,() ) )) for k in set(val)|set(old) ]
                    diff=[k for k in diff if k[1]]
                    if diff:
                        print 'Change in TxtImport:',item.__class__, diff
                else:
                    setattr(item,key,val)
        for i,j in infos.iteritems():
            item=items[i]
            for k,v in j.iteritems():
                key,val=[self.testrev(x,items,1) for x in (k,v)]
                added=item.add(key,addrequired=True, **val)
                if not added:
                    if key in item.infos:
                        item.infos[key].update(val)
                        #for x,y in val.iteritems()
                            #item.set_info(key,x,y)
                    else:
                        print 'Not added:', item, key, val
                        raise Exception('Adding error')
        fd.close()

    def context_trans(self,item,dic):
        #translates objects between contexts
        if not hasattr(item,'truename'):
            return item
        return dic.get( item.truename,None)


    def add_context(self,context):
        #A context is an underlying infosource that can be accessed by transparency
        #but should not be saved together with this data object (e.g. because
        #it comes from the database of the entire game)
        #Since they are not saved together, references to the same object
        #here and in the data source for the context must be indicated by
        #a unique and permanent identifier
        rcontext=context.__class__()
        rcontext.context_origin=context
        dic={i.truename:i for i in self.infos if hasattr(i,'truename') }
        for j in context.infos:
            rcontext.infos[j]=shallow_nested(context.infos[j],
                        meth=lambda e,d=dic:self.context_trans(e,d))
            ref=None
            for iname,i in dic.iteritems():
                if iname==j.truename:
                    rcontext.infos[i]=rcontext.infos[j]
        self.contexts+= rcontext,

    def rem_context(self,context):
        self.contexts=(c for c in self.contexts if c.context_origin!=context)


class DataBit(object):
    #Urstructure of DataItem, cannot be the subject of information in a structure
    dft={}
    nested_copy=1
    #If I make a copy of some object with this DataBit as one of its fields,
    #create instead a copy of the DataBit (i.e. behaves like tuple rather than list)
    #Set to 1 only if this DataBit is #never# used as reference
    #(thus false for DataItems that are used as reference in Data)


    def __init__(self,**kwargs):
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
        if hasattr(self,'klass_name'):
            klassn=self.klass_name
        else:
            klassn=self.__class__.__name__

        if not id(self) in keydic:
            keydic[id(self)]=len(keydic.keys() )
            typdic.setdefault(klassn,[]).append(keydic[id(self)])
        txt="#{}#\n ##class:{}\n ##initparam:{}\n".format(
            keydic[id(self)],klassn,init_param)
        test=lambda e:Data().testport(e,keydic,txtdic,typdic)
        for i in set(sorted(self.dft))|set(add_param):
            if not hasattr(self,i):
                print 'ERROR: {} has no attr {}'.format(self,i)
                continue
            tmp='{}:{}\n'.format(test(i),test(getattr(self,i)))
            txt+=tmp
        txt+='##\n'
        txtdic[keydic[id(self)]]=txt

    def txt_import(self):
        pass

class DataItem(DataBit):

    required=() #=This dataitem can exist in a data structure only if all the required items are already there
    ID=None #ID given to it by the data structure
    nested_copy=0
    def __init__(self,**kwargs):
        if not hasattr(self,'type'):
            self.type='dataitem'
        DataBit.__init__(self,**kwargs)

    def txt_export(self,keydic,txtdic,typdic,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']=set(kwargs['add_param'])
        kwargs['add_param'].update(set(['required','ID']))
        if hasattr(self,'truename'):
            kwargs['add_param'].add('truename')
        DataBit.txt_export(self,keydic,txtdic,typdic,**kwargs)

