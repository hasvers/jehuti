# -*- coding: utf-8 -*-

#
from gam_import import user
import weakref


class DataWorld(object):
    '''
    Contains the permanent version (essence) of all DataItems in the game.
    Receives messages from each subsystem when they need to import
    something (creating an avatar) or when they are merging something back.

    Since every DataItem has a unique name here, they can be referred to in
    scripts.
    '''

    def __init__(self):
        self.name={}
        self.item={}
        self.manager={} #The dataset that manages some essence (usually its creator)
        #                or some avatar
        self.permissions={}
        self.essence={}
        self.avatars={}
        self.script_refers_to={}
        self.waiting_for_essence={} #In case a scene with avatars is loaded before
        #the node containing the essence, esp. when loading the full game.

        #self.appears_in={} #Scenes in which an avatar appears

    def __getitem__(self,name):
        return self.item[name]

    def get_infotypes(self,itemtype,**kwargs):
        '''Very hackish way of dealing with calls to DataWorld as precursor
        (cf gv_data).'''
        for item in self.avatars:
            if item.type==itemtype:
                return self.manager[item].get_infotypes(item.type,**kwargs)
        return ()

    def get_info(self,item,*args,**kwargs):
        '''When the DataWorld is used as a context by data structures in
        subsystems, it goes fetch information .'''
        if not item in self.essence:
            return None
        e=self.essence[item]
        if e in self.manager:
            return self.manager[e].get_info(e,*args,**kwargs)
        return None

    def set_info(self,*args,**kwargs):
        #TODO: It should be possible to set info when the caller is not
        #the manager but has the appropriate permission
        return False

    def declare(self,caller,item):
        '''When an item is created in a subsystem, it is declared to the world.
        In general its name at creation is bland, hence it should be updated '''
        if item in self.essence:
            print 'Item {} already declared'
            return False
        #print 'declaring',caller,item
        self.essence[item]=item
        self.avatars[item]=[]
        self.manager[item]=caller
        if hasattr(item,'truename'):
            name=item.truename
        elif hasattr(item,'name'):
            name=item.name
        else:
            name=str(item)
        if name in self.item:
            name+=str(id(item))
            item.truename=name
            print 'CAUTION: Duplicate in truenames: {} has been updated to {}'.format(
                self.item,name)
        self.name[item]=name
        self.item[name]=item
        self.script_refers_to[name]=weakref.WeakSet()
        self.attribute_essence(name)
        #self.appears_in[item]=[caller]

    def attribute_essence(self,name):
        if name in self.waiting_for_essence and name in self.item:
            item=self.item[name]
            #print 'found essence', name
            for avatar in self.waiting_for_essence[name]:
                self.avatars[item].append(avatar)
                self.essence[avatar]=item
            del  self.waiting_for_essence[name]

    def update_name(self,caller,item,name,force=False):
        '''When the name of an item changes in the manager subsystem,
        try to update it here unless that would create a duplicate.'''

        #print 'update',caller,item,name
        if not force and caller!= self.manager[item]:
            raise Exception('Caller {} is not allowed to rename item {}'.format(
                caller,item))

        if name in self.item:
            #New name already exists
            print 'CAUTION: Name {} already exists in DataWorld'.format(name)
            return False

        #Update the name
        oldname=self.name[item]
        for s in self.script_refers_to[oldname]:
            self.update_python_script(oldname,name)
        managers=[]
        for a in self.avatars[item]:
            #print 'updating',a,a.truename,'to',name
            a.truename=name
            managers.append(self.manager[a])
        if managers:
            leg='''Items in the following data structures have changed:\n   '''
            leg+='\n   '.join([  str(c.name) for c in managers])
            leg+="\nDo you want to save them?"
            savmeth=lambda h=managers:[c.save() for c in h]
            user.ui.confirm_menu(savmeth,pos='center',legend=leg)
        self.name[item]=name
        del self.item[oldname]
        self.item[name]=item
        self.script_refers_to[name]=weakref.WeakSet()
        self.attribute_essence(name)

    def declare_python_script(self,script):
        '''Declare a python script that refers to an object by name,
        so that the script is updated if the name changes.
        Maybe this is not such a good idea.'''
        txt=script.text
        for name in self.item:
            if name in txt:
                self.script_refers_to[name].add(script)

    def undeclare_python_script(self,script):
        txt=script.text
        for name in self.item:
            if name in txt:
                self.script_refers_to[name].remove(script)

    def do_python_script(self,script,mode='eval'):
        if isinstance(script,basestring):
            text=script.text
        else:
            text=script
        if mode=='exec':
            exec(text, globals(), self.name)
        else:
            return eval(text, globals(), self.name)


    def get_essence(self,name_or_item):
        if name_or_item in self.name:
            item=self.name[name_or_item]
        else:
            item=self.item
        return self.essence[item]

    def avatar(self,name_or_item):
        if name_or_item in self.name:
            item = name_or_item
        else:
            item = self.item[name_or_item]
        avatar= item.copy()
        avatar.truename=self.name[item]
        self.avatars[item].append(avatar)
        self.essence[avatar]=item
        return avatar

    def detect_avatars(self,data,handler):
        '''Search a datastructure for items that would be avatars
        of some existing essence.'''
        for avatar in data.infos:
            if not hasattr(avatar,'truename'):
                continue
            #print 'found avatar',avatar

            if not avatar in self.essence:
                if avatar.truename in self.item:
                    #print 'found essence'
                    item=self.item[avatar.truename]
                    self.avatars[item].append(avatar)
                    self.essence[avatar]=item
                else:
                    #print 'waiting for essence',avatar,avatar.truename,self.item
                    self.waiting_for_essence.setdefault(avatar.truename,[]).append(avatar)
                if not handler is None:
                    self.manager[avatar]=handler
                else:
                    self.manager[avatar]=data