# -*- coding: utf-8 -*-
from gam_rules import *


class Logic(object):

    def __init__(self,rules):
        self.rules=rules

    def truth_check(self,val,cond):
        if cond=='all':
            return True
        if cond =='+' and self.rules.truth_value(val)>0:
            return True
        if cond =='-' and self.rules.truth_value(val)<0:
            return True
        if cond =='?' and self.rules.truth_value(val)==0:
            return True
        return False

    def concord(self,linf,ninf1,ninf2):
        logic=linf['logic']
        tv=self.rules.truth_value
        t1,t2=tv(ninf1['truth'])*tv(logic[0]),tv(ninf2['truth'])*tv(logic[1])
        #print '\nConcord',t1,t2,logic,ninf1['truth'],ninf2['truth']
        if t1 >0 and t2 >0:
            return 'full'
        if t1<0 and logic[2] and t2<=0:
            return 'srcneg'
        if t2<0 and logic[3] and t1<=0:
            return 'tgtneg'
        return 0


class TextBase(object):
    def __init__(self,scene=None):
        self.rules=MatchRuleset(scene)
        self.scene=scene
        self.logic=Logic(self.rules)


class TextGen(TextBase):
    '''Class to generate text content automatically for entities'''

    node_descriptor={
            'Narrative': ('anecdote','story'),
            'Statement': ('remark','fact'),
            'Formalism':('hypothesis','theory'),
            'Speculation':('idea','speculation'),
            'Prescription':('code','law','tradition'),
            'Poetry':('aphorism','poem')
            }
    def node_text_generator(self,genre,magnitude):
        idx=0
        if magnitude>1.:
            idx=1
        desc= self.node_descriptor[genre][idx]
        declaration='a'
        if desc[0] in 'aeiou':
            declaration+='n'
        declaration+=' '+desc
        desc='This is '+declaration+'.'
        name=declaration.capitalize()
        ninfo={
            'desc':desc,
            #'quotes':[ConvQuote(declaration)],
            'name':name
            }
        return ninfo

    def link_text_generator(self,pattern,magnitude,parent_genres):
        desc=pattern.lower()
        declaration='a'
        if desc[0] in 'aeiou':
            declaration+='n'
        declaration+=' '+desc
        desc='This is '+declaration+'.'
        ninfo={
            'desc':desc
            }
        return ninfo


    def ethos_effect_name(self,infos):
        val=copysign(1,infos['val'])
        res=infos['res']
        tgt=infos['target']

        txts={('face','claimer',-1):'Apologetic',
            ('face','claimer',1):'Clever',
            ('face','hearer',-1):'Offensive',
            ('face','hearer',1):'Flattering',
            ('terr','claimer',-1):'Committed',
            ('terr','claimer',1):'Confident',
            ('terr','hearer',-1):'Intimate',
            ('terr','hearer',1):'Concessive',
            ('path','claimer',1):'Emotional',
            ('path','claimer',-1):'Rational',
            }
        return txts[(res,tgt,val)]


class TextTools(TextBase):
    '''General usage text treatment tools.'''

    def actor_name(self,actor):
        try:
            name='%c'+str(actor['color'])+'%'
        except:
            name= '%c(255,150,150,255)%'
        name+= actor['name'] + '%%'
        return name



class TextInteract(TextBase):

    def nonverb_agreement(self,actor,agreement,mode='Agree'):
        dic={ 'Agree':{'+':'nods','?':'shrugs','-':'frowns' }  ,
            'Convinced':{'+':'appears convinced','?':'seems undecisive','-':'seems skeptical' } ,
        }
        dic=dic[mode]
        #name=' ' +actor['name']
        ainf=self.scene.get_info(actor)
        if ainf.get('react',None):
            reacs=[]
            for r in ainf['react']:
                if r.test_cond(agreement,mode):
                    reacs.append(r)
            if reacs:
                return rnd.choice(reacs).text
        if agreement <0 :
            txt=dic['-']
        elif agreement ==0 :
            txt=dic['?']
        else:
            txt=dic['+']
        return '*{}*'.format(txt)
    def nonverb_conviction(self,actor,agreement):
        return self.nonverb_agreement(actor,agreement,mode='Convinced')


    def makeverb_agreement(self,actor,agreement,mode='Agree'):
        dic={ 'Agree':{'+':'I agree','?':'Perhaps','-':'No' }  ,
            'Convinced':{'+':'This seems reasonable','?':'I should think more about this',
                '-':'This seems doubtful' } ,
        }
        dic=dic[mode]
        #name=' ' +actor['name']
        ainf=self.scene.get_info(actor)
        if ainf.get('react',None):
            reacs=[]
            for r in ainf['react']:
                if r.test_cond(agreement,mode):
                    reacs.append(r)
            if reacs:
                return rnd.choice(reacs).text
        if agreement <0 :
            txt=dic['-']
        elif agreement ==0 :
            txt=dic['?']
        else:
            txt=dic['+']
        return '"{}."'.format(txt)


    def interpret(self,stage):
        '''Treats an interpretive stage: sum of perceived reactions that may include
reaction to premise, to conclusion, to argument itself, and so on.'''
        print 'INTERPRET:', stage.verbal, stage.nonverbal,stage.mean
        scene=self.scene
        txt=''
        if stage.verbal:
            agreement=stage.mean[0]
            mode='Agree'
            if True in [i.discovery for i in stage.nonverbal]:
                mode='Convinced'
            txt+=self.makeverb_agreement(stage.actor,agreement,mode)
        else:
            agreement=stage.mean[0]
            mode='Agree'
            if True in [i.discovery for i in stage.nonverbal]:
                mode='Convinced'
            txt+=self.nonverb_agreement(stage.actor,agreement,mode)
        return txt

    def selfreac(self,stage):
        scene=self.scene

    def claim(self,stage):
        scene=self.scene
        #TODO: MAKE PROPER AUTOTEXT
        infos=scene.canvas.get_info(stage.item)
        txt=''
        if  stage.type=='claim' and stage.item.type=='node':
            if infos.get('desc'):
                txt=infos['desc']
            else:
                txt=infos['name']
        return txt