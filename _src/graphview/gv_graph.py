# -*- coding: utf-8 -*-
import networkx as netx
from gv_component import *

class Node(DataItem):
    nid=0
    genres=database['node_genres']
    klass_name='Graph.Node'
    dft={'name':'Node',
        'genre':genres[0],
        'val':1.,
        'desc':'',
        }

    def __init__(self,**kwargs):
        self.type='node'
        DataItem.__init__(self,**kwargs)
        self.nid=self.__class__.nid
        self.__class__.nid+=1


    def __str__(self):
        if self.ID!=False:
            return 'Node '+str(self.ID)
        else :
            return 'Node Abs'+str(self.nid)


class Link(DataItem):
    lid =0
    genres=database['link_genres']
    klass_name='Graph.Link'
    dft={'name':'Link',
        'genre':genres[0],
        'val':.5,
        'desc':'',
        }
    _required=None

    def __init__(self,parents,**kwargs):
        self.type ='link'
        self.parents=parents
        DataItem.__init__(self,**kwargs)
        self.lid =self.__class__.lid
        self.__class__.lid+=1

    @property
    def required(self):
        if self._required!=None:
            return self._required
        else:
            return self.parents

    @required.setter
    def required(self,val):
        self._required=val

    def txt_export(self,keydic,txtdic,typdic,**kwargs):
        kwargs.setdefault('add_param',[]).append('parents')
        kwargs.setdefault('init_param',[]).append('parents')
        return DataItem.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def other_parent(self,parent):
        '''Find who is at the other end of a link'''
        if not parent in self.parents:
            return ()
        oth=[p for p in self.parents if p!=parent]
        if len(oth)==1:
            return oth[0]
        else:
            return oth

    def __str__(self):
        return 'Link '+str(tuple(n.ID for n in self.parents))



class Subgraph(Data):
    """Subset of the parent graph with additional info, but contains nothing in itself."""

    name='dft_subgraph'
    klass_name='Graph.Subgraph'
    infotypes={
        'node':
            (
                'desc',
            ),
        'link':
            (
                'desc',
            ),
        }
    rule='none'
    fakelists=('links')#,'nodes')
    transparent=True
    overwrite_item=False
    def __init__(self,parent,**kwargs):
        '''A subgraph is a subset of a fundamental graph.
        Items are either added by hand, or automatically from
        the parent provided they pass the should_contain test
        which relies on rule. Rules are either:
            - lambdas, tuples ('item_type',lambda)
            - strings 'all', 'info_type <>=!= value'. '''

        self.links={}
        self.nodes=[]
        Data.__init__(self,parent=parent,maketypedlists=False,**kwargs)
        if self.rule :
            self.import_from_parent()

    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[]).append('rule')
        kwargs.setdefault('init_param',[]).append('parent','rule')
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

    def __str__(self):
        #if self.name != Graph.Subgraph.name :
            #return 'Subgraph:'+self.name +'('+unicode(self.parent)+')'
        return 'Subgraph('+unicode(self.parent)+')'

    def renew(self):
        Data.renew(self)
        self.links={}

    def add(self,item,**kwargs):
        #print self, item
        if Data.add(self,item,**kwargs):
            if item.type =='node':
                self.links[item]=[]
            if item.type =='link':
                for p in item.parents :
                    if p in self.links:
                        self.links[p].append(item)
            return True
        return False

    def set_info(self,item,ityp,val,**kwargs):
        if Data.set_info(self,item,ityp,val,**kwargs):
            if item.type=='node' and not item in self.nodes and item in self.infos:
                print 'ERROR gv_graph: Node in infos but not in nodes.', item, ityp, val,self, debug.caller_name()
#                self.nodes.append(item)
            return True
        return False

    def remove(self,item):
        done=False
        if not item in self.infos:
            return done
        if item.type=='node':
            del self.links[item]
            done = True
        elif item.type =='link':
            for p in item.parents :
                if p in self.links :
                    try:
                        self.links[p].remove(item)
                    except:
                        pass
            done = True
        if done :
            [c.remove(item) for c in self.children]
            Data.remove(self,item)
        return done

    def rewire(self,link,newparents=None,oldparents=None):
        for p in oldparents:
            if p in self.links :
                if link in self.links[p]:
                    self.links[p].remove(link)
        for p in newparents:
            if p in self.infos :
                if p in self.links :
                    self.links[p].append(link)
            else :
                self.remove(link)
                return False

class Graph(Data):

    """ Minimal class for graphs if no interface with exterior model"""

    name='dft_graph'
    datatype='graph'
    infotypes={
        'node':(
            'name',
            'genre',
            'val',
            'desc',),
        'link':(
            'name',
            'genre',
            'val',
            'desc',),
        }
    fakelists=('links')
    overwrite_item=True
    def __init__(self,**kwargs):
        self.nodes=[]
        self.links={}
        Data.__init__(self,**kwargs)
        self.pos={}

    Node= Node
    Link= Link
    Subgraph= Subgraph

    def __str__(self):
        if self.name:
            return 'Graph:'+self.name

    def add(self,item,**kwargs):
        if Data.add(self,item,**kwargs):
            if item.type =='node':
                self.links[item]=[]
            if item.type =='link':
                for p in item.parents :
                    if p in self.links: #unless p is a linkgrabber or other beast
                        self.links[p].append(item)
            return True
        return False

    def renew(self,*args):
        Data.renew(self,*args)
        self.links={}
        self.pos={}

    def make(self,**kwargs):
        N=kwargs.pop('N',40)
        self.renew(False)

        print 'Making new graph'
        G=netx.watts_strogatz_graph(N,4,0.3)
        size=ergonomy['default_canvas_size']
        print netx.info(G)
        for n in G.nodes():
            self.add(self.Node(val=rnd.uniform(0.8,1.4)))
        for l in G.edges_iter() :
            n1,n2=l
            if n1!= n2 :
                self.add(self.Link((self.nodes[n1],self.nodes[n2])),val=rnd.uniform(0,1))
        self.pos=dict([ (self.nodes[i],[int(k*s) for k,s in zip(list(j),size)])
            for i,j in netx.spring_layout(G).iteritems()])

    def rewire(self,link,newparents):
        oldparents=link.parents[:]
        for p in oldparents:
            if p in self.links :
                self.links[p].remove(link)
        for p in newparents:
            self.add(p)
            if p in self.links :
                self.links[p].append(link)
        link.parents= newparents
        for c in self.children :
            c.rewire(link,newparents,oldparents)

    def remove(self,item):
        done=False
#        if not item in self.infos:
#            return done
        if item.type=='node':
            del self.links[item]
            del self.pos[item]
            done = True
        elif item.type =='link':
            for p in item.parents :
                if p in self.links and item in self.links[p]:
                    self.links[p].remove(item)
            done = True
        if done :
            [c.remove(item) for c in self.children]
            Data.remove(self,item)
        return done

    def rem_subgraph(self,subgraph):
        try :
            self.children.remove(subgraph)
            if subgraph.parent==self:
                subgraph.parent=None
        except :
            pass


    def contains(self,item):
        if item.type == 'node':
            if item in self.nodes :
                return True
        if item.type =='link':
            if item.parents[0] in self.links:
                if item in self.links[item.parents[0]] :
                    return True
        return False


    def txt_export(self,keydic=None,txtdic=None,typdic=None,**kwargs):
        kwargs.setdefault('add_param',[])
        kwargs['add_param']+=['pos']
        return Data.txt_export(self,keydic,txtdic,typdic,**kwargs)

