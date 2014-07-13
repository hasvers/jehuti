# -*- coding: utf-8 -*-

from gam_rules import *

class TextBase(object):
    def __init__(self,match=None):
        self.rules=MatchRuleset(match)
        self.logic=Logic(self.rules)

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
            'quotes':[ConvQuote(declaration)],
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

class Semantics(object):

    def __init__(self):
        pass

    #eventually, anaphor will go beyond a single batch and chain the conversation together
    def batch_segment(self,batch):
        firstmention={}
        new=[]
        items={}
        #links=[]
        #lst={'node':nodes,'link':links}
        struct=nx.MultiDiGraph()
        for e in batch.root_events:
            if 'claim' in e.type:
                item=e.item
                #if item in firstmention:
                    #if e.is_discovery:
                        #raise Exception('badly ordered claims')
                    #continue #TODO:Think about this
                items[e]=[item]
                firstmention[item]=e
                #lst[item.type].append(item)
                struct.add_node(e)
                #if e.is_discovery:
                new.append(item)
                for it in item.required+tuple(s.item for s in e.subclaims if not s.item in item.required):
                    #eventually, change this into recursive
                    items[e].append(it)
                    if not it in firstmention:
                        firstmention[it]=e
                    else:
                        struct.add_edge(firstmention[it],e,key=it)
                for s in e.subclaims:
                    new.append(s.item)
        return firstmention,new,items,struct #each group in struct must be treated as a whole

    def batch_analysis(self,batch,graph,logic):
        inf =graph.get_info
        rules=logic.rules
        firstmention,new,items,struct=self.batch_segment(batch)
        if not firstmention:
            return [],[]
        #else:
            #print firstmention,new,items,struct.nodes()
        truth={}
        concord={}
        focus={}
        for i in firstmention.keys():
            if i.type=='node':
                truth[i]=rules.truth_value(inf(i,'truth'))
            else:
                concord[i]=logic.concord(inf(i),inf(i.parents[0]),inf(i.parents[1]) )

        clusters=[]
        undir=nx.Graph()
        for e in struct.edges_iter(None,0,1):
            c1,c2,n=e
            t1,t2=c1.item.type,c2.item.type
            if t1==t2=='link':
                if concord[c2.item] and concord[c2.item]:
                    sem='Both'
                elif not concord[c2.item] and not concord[c2.item] :
                    sem='Neither'
                else:
                    sem='Contrast'
            else:
                sem='Source'

            struct.edge[c1][c2]['sem']=sem
            undir.add_edge(c1,c2)

        for c in struct.nodes():
            if struct.predecessors(c):
                continue
            if c in undir.nodes():
                clus=struct.subgraph(nx.node_connected_component(undir, c))
            else:
                clus=struct.subgraph([c])
            cn=[i for cc in clus.nodes() for i in items[cc] if i.type=='node']
            cl=[i for cc in clus.nodes() for i in items[cc] if i.type=='link']
            ce={}
            for i in struct.edges_iter(None,0,1):
                ce.setdefault(i[2],[]).append(i[:2])
            for n in cn:
                if n in focus:
                    continue
                f=cn.count(n)
                if n in new:
                    f+=1
                if truth[n]!=0:
                    f+=1
                for link in cl:
                    genre=inf(link,'genre')
                    if n==link.parents[0] and genre=='Context':
                        f-=5
                focus[n]=f
            #fn=sorted(cn,key=lambda e:focus[e],reverse=1)
            #TODO? : potentially some ordering here??
            #while fn:
                #topic=fn[0]
                #e=firstmention[topic]
                #for edge in ce.get(topic,[]):
                    ##TODO
                    #pass
                #break
            clusters.append(clus)
        data={}
        for i in firstmention.keys():
            data[i]={}
            if i in truth:
                data[i]['truth']=truth[i]
            if i in focus:
                data[i]['focus']=focus[i]
            if i in concord:
                data[i]['concord']=concord[i]
            if i in new:
                data[i]['new']=1
            data[i]['clusteranchor']=firstmention[i]
        return clusters, data

### If the premise is new, first state the premise

### If the premise is old but the conclusion new, first state the conclusion
### Then add link as "as expected from" or "despite the fact that"  depending on
### whether the premise agrees with the conclusion or not.

#if the same node is present in multiple claims, with agreement or concordance in some
# and not in others, use contrastive

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




class TextMaker(object):

    def __init__(self,match=None):
        self.rules=MatchRuleset(match)
        self.logic=Logic(self.rules)


    def agreement_reaction(self,actor,agreement,mode='Agree'):
        dic={ 'Agree':{'+':'nods','?':'shrugs','-':'frowns' }  ,
            'Convinced':{'+':'appears convinced','?':'seems undecisive','-':'seems skeptical' } ,
        }
        dic=dic[mode]
        #name=' ' +actor['name']
        name=''
        if actor['react']:
            reacs=[]
            for r in actor['react']:
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
    def convincing_reaction(self,actor,agreement):
        return self.agreement_reaction(actor,agreement,mode='Convinced')

    def reac_say(self,actor,graph,batch,**kwargs):
        sem=kwargs.get('sem',{})
        eff=kwargs.get('eff',{})
        cluster=nx.Graph()
        cluster.add_nodes_from([i.parent for i in batch.events])
        cluster=kwargs.get('cluster',cluster)
        vals={}
        done=[]
        for i in ('prem','conc','new','gen','useful'):
            vals[i]=[0,0,0]
        txt=''
        for e in batch.rec_events:
            if 'reac' in e.type and sem.get(e.item,{}).get('clusteranchor') in  cluster.nodes() :
                item=e.item
                for q in graph.get_info(item,'quotes'):
                    if q.cond =='Reac':
                        if item.type=='link' or item.type=='node' and self.logic.truth_check(
                            e.parent.decl.kwargs['truth'],q.truth):
                            txt+=q.val
                #print e, e.kwargs['agreement']
                w=sem.get(item,{}).get('focus',1)
                done.append(item)
                if item.type=='node':
                    lls=['gen']
                    if e.is_discovery:
                        lls.append('new')
                    for n in cluster.nodes():
                        if n.item.type=='link':
                            if item==n.item.parents[0]:
                                lls.append('prem')
                            elif item==n.item.parents[1]:
                                lls.append('conc')
                    for c in lls:
                        vals[c][e.kwargs['agreement']+1]+=w
                else:
                    vals['useful'][(sem.get(item,{}).get('concord')!=0)*2]+=1
                    tv=self.rules.truth_value
                    for idx,i in enumerate(item.parents):
                        if not i in done:
                            tt=1+tv(graph.get_info(i,'truth'))*sem.get(i,{}).get('truth')
                            vals[['prem','conc'][idx] ][tt]+=1
        #print vals, actor['name']
        if txt or database['demo_mode']:
            return txt
        fin={}
        for i,j in vals.iteritems():
            vals[i]=array(j)
            fin[i]=(j[2]-j[0])
            if j[1]:
                fin[i]/=float(j[1])
            if fin[i]>=1:
                fin[i]=1
            elif fin[i]<=-1:
                fin[i]=-1
            else:
                fin[i]=0
        order=sorted([i for i in vals],key=lambda e:sum(vals[e]),reverse=1)
        reacs={0:'I am hazy on ',1:'I agree with ',-1:'I disagree with '}
        txt=''
        #print fin
        if database['demo_mode']:
            if order[0]=='new':
                txt=self.agreement_reaction(actor,fin['new'],'Convinced')
            else:
                txt=self.agreement_reaction(actor,fin['gen'],'Agree')
            return txt

        if order[0]=='useful':
            if fin['useful']<0:
                return 'This is not very conclusive.'
            order.pop(0)
        if order[0] in ('prem','conc'):
            if fin['prem']==fin['conc']:
                txt= ''
            else:
                txt='{} your premises but {} your conclusion.'.format(reacs[fin['prem']] ,reacs[fin['conc']])
        if not txt:
            if order[0]=='new':
                txt=self.agreement_reaction(actor,fin['new'],'Convinced')
            else:
                txt=self.agreement_reaction(actor,fin['gen'],'Agree')
        return txt

    def actor_name(self,actor):
        try:
            name='#c'+str(actor['color'])+'#'
        except:
            name= '#c(255,150,150,255)#'
        name+= actor['name'] + '##'
        return name

    def clean_text(self,txt):
        #This is where I capitalize and regularize "" and everything
        return txt

    def batch_declaration(self,actor,graph,batch):
        clusters,semdata=Semantics().batch_analysis(batch,graph,self.logic)
        ct=[]
        for c in clusters:
            ct.append(self.cluster_say(actor,graph,c,semdata))
        return clusters,semdata,ct

    def cluster_say(self,actor,graph,cluster,semdata):
        mentioned=[]
        txt=''
        preve=None
        for e in cluster.nodes():
            if not preve is None:
                connec='Besides, '
                try:
                    sem=cluster.edge[preve][e]['sem']
                    if sem=='Both':
                        if preve.item.parents[1]==e.item.parents[0]:
                            connec=''
                        elif preve.item.parents[0]==e.item.parents[1]:
                            connec='Indeed, '
                        else:
                            connec='Likewise, '
                    if sem=='Neither':
                        connec='And '
                    if sem=='Contrast':
                        connec='On the other hand, '
                    if sem=='Source':
                        connec=''
                except:
                    pass
            else:
                connec=''
            txt+=connec
            preve=e
            item=e.item
            if item.type=='node':
                etxt=self.node_declaration(actor,graph.get_info(item))
                mentioned.append(item)
            if item.type=='link':
                p1,p2=item.parents
                if semdata[p1]['focus']>semdata[p2]['focus']:
                    theme,rheme,topic=p1,p2,0
                else:
                    theme,rheme,topic=p2,p1,1
                mode=['N','N']
                #if semdata[theme].get('new',0):
                mode[topic]='S'
                if mentioned:
                    if theme in mentioned[-2:]:
                        mode[topic]='Ana'
                    elif rheme==mentioned[-1]:
                        mode[1-topic]='Ana'
                mentioned.extend([rheme,theme])

                etxt=self.link_say(actor,item,graph.get_info(p1),graph.get_info(p2),graph,
                    topic=topic,concord=semdata[item]['concord'],mode=mode,bestmode=1)
                if not connec and etxt[0]!='"':
                    etxt=etxt.capitalize()
            txt+=etxt
            if txt[-1] not in ('.','"'):
                txt+='. '
        return self.clean_text(txt)

    def txtpatterns(self):
        dedpat0={
            'full':['[N] entails [N]','[N] implies that [S]','[S], which entails [N]','[S], therefore [S]'],
            'srcneg':['[S], leaving the possibility that [S]','[N] allows [N]'],
            'tgtneg':['[S], suggesting that [S]'],
            0:['although [S], [S]', 'despite [N], [S]'],
            }
        dedpat1={
            'full':['[N] ensues from [N]','[S], due to [N]','[S], since [S]'],
            'srcneg':['[S],  [S]','[N] does not contradict [N]'],
            0:['[S] although [S]', '[S] despite [N]'],
            }
        conpat0={'full':['[S], hence [N] is {t-:ir}relevant','[S], so [S]','[N] shows the {t-:ir}relevance [N]'],
            0:['although [S], you should note that [S]']
            }
        conpat1={'full':['[N] is {t-:ir}relevant because of [N]',
                            '{t-:while }[S], {t-:it}{t+:which} is {t-:ir}relevant because of [N]',
                            '{t-:while }[S], {t-:it}{t+:which} is {t-:ir}relevant because [S]',
                            '[N] is {t-:ir}relevant because [S]'],
            0:['[S], {t+:but it}{t):which} is {t+:ir}relevant although [S]']
            }
        evopat0={'full':['[S], which is an example of [N]','[S]. This shows how [S]','[N] exemplifies [N]'],
            0:['[S]. nevertheless [S]']
            }
        evopat1={'full':['[S], for example [N]','[S], for example [S]'],
            0:['although [S], [S]']
            }
        txtpatterns={'Deduction':{0:dedpat0,1:dedpat1},
            'Context':{0:conpat0,1:conpat1},
            'Evocation':{0:evopat0,1:evopat1}}
        return txtpatterns

    def link_say(self,actor,item,ninfo1,ninfo2,graph,**kwargs):
        info=graph.get_info(item)
        for q in graph.get_info(item,'quotes'):
            if q.cond=='Default':
                return q.val
        print 'Missing link text', item, actor
        return '...'
        genre=info['pattern']
        logic=info['logic']
        concord=kwargs.get('concord','full')
        topic=kwargs.get('topic',0)
        mode=kwargs.get('mode',None)
        bestmode=kwargs.get('bestmode',0)
        if mode is None:
            mode=['N','N']
        tmpmode=tuple(i.replace('Ana','N') for i in mode)
        available={}
        for txt in self.txtpatterns()[genre][topic][concord]:
            pat= tuple(i.replace('[','').replace(']','') for i in re.findall("\[.*?\]",txt))
            available.setdefault(pat,[]).append(txt)
        if bestmode:
            pats=[]
            for pat in available:
                tmp=[self.node_say(actor,ninfo1,mode=pat[topic]),self.node_say(actor,ninfo2,mode=pat[1-topic])]
                score=sum(1== t[1][1] for t in tmp) + 3*sum(pat[i]=='N' for i in (0,1) if mode[i]=='Ana')
                pats.append((score,pat,tmp))
            i,tmpmode,nsayc=sorted(pats,key=lambda e:e[0])[-1]
        elif tmpmode not in available:
            tmpmode=available.keys()[0]
        for i,j in enumerate(tmpmode):
            if  mode[i]!='Ana':# or tmpmode[i]!='N': #Keep 'Ana' of initial mode if possible
                print mode, pats
                mode[i]=tmpmode[i]
        nsayc=[self.node_say(actor,ninfo1,mode=mode[0]),self.node_say(actor,ninfo2,mode=mode[1])]
        nsay=[]
        for ic,nc in enumerate(nsayc):
            n,corr=nc
                #Grammatical conversion
                #ACTUALLY NOT ALWAYS NECESSARY, I should dispense from it when
                #I have a fitting grammatical scheme below
            nsay.append(self.node_txtconvert(n,[ninfo1,ninfo2][ic],corr,mode=mode[ic]))
            if mode[ic]=='Ana' and not corr[1]:
                nsay[ic]='this'

        txt=rnd.choice(available[tmpmode]).replace('[{}]'.format(tmpmode[topic]),nsay[topic],1)
        txt=txt.replace('[{}]'.format(tmpmode[1-topic]),nsay[1-topic],1)
        pats=re.findall("{.*?}",txt)
        for p in pats:
            if not p:
                continue
            pat=p[1:-1].split(':')
            if pat[0][0]=='s':
                val=logic[0]
            elif pat[0][0]=='t':
                val=logic[1]
            if self.logic.truth_check(val,pat[0][1]):
                txt=txt.replace(p,pat[1])
            else:
                txt=txt.replace(p,'')
        return txt
        #topic=self.node_say(actor,ninfo1)

    def node_txtconvert(self,txt,info,corr,**kwargs):
        #Grammatical conversion:
        mode=kwargs.get('mode','S') #S/NP
        #print'===',  mode, corr, txt, info
        if mode=='S':
            if corr[1]:
                if not corr[0]:
                    if  self.logic.truth_check(info['truth'],'-'):
                        txt= "I don't think that {}".format(txt)
                    elif self.logic.truth_check(info['truth'],'?'):
                        txt= "I am unsure whether {}".format(txt)
            else:
                #TODO:replace by nodegenre-dependent sentence (X is true, X is right...)
                if corr[1]:
                    txt= "I claim {}".format(txt)
                if corr[0]:
                    txt= "I dispute {}".format(txt)
        if mode=='N':
            if corr[1]: #txt IS a NP
                if not corr[0]: #but with wrong truth value
                    if self.logic.truth_check(info['truth'],'?'):
                        txt='the uncertainty of {}'.format(txt)
                    else:
                        txt='the falsity of {}'.format(txt)
            else:
                txt='the fact that {}'.format(txt)
        return txt

    def node_say(self,actor,info,**kwargs):
        mode=kwargs.get('mode',None) #S (children are innocent)/ NP (children being innocent/A child's innocence)
        mode_marked=0
        if not mode is None:
            mode_marked=1
        else:
            mode='S'
        quotes=info.get('quotes',[])

        candidates=[]
        for q in quotes:
            txt= q.val
            corr=[0,0] #truth/mode
            if '{' in txt:
                #REGEXP
                pats=re.findall("{.*?}",txt)
                for p in pats:
                    if not ':' in p:
                        if p[1:-1] in text_bank['templateverbs']:
                            for i,j in text_bank['templateverbs'][p[1:-1]].iteritems():
                                if self.logic.truth_check(info['truth'],i[0]):
                                    txt=txt.replace(p,j)
                                    corr[0]=1
                                if mode==i.replace('+','').replace('-','').replace('?',''):
                                    txt=txt.replace(p,j)
                                    corr[1]=1
                        else:
                            txt.replace(p,p.replace('{','').replace('}',''))
                        if mode is None:
                            corr[1]=1
                    else:
                        pat=p[1:-1].split(':')
                        if len(pat[0])>1:
                            t=pat[0][0]
                            c=pat[0][1:]
                        else:
                            t=pat[0]
                            c=None
                        if self.logic.truth_check(info['truth'],t):
                            corr[0]=1
                        if c==mode:
                            corr[1]=1
                        if array(corr).any():
                            txt=txt.replace(p,pat[1])
                        else:
                            txt=txt.replace(p,'')
            conds=mode=='S' and q.cond in ('Default','Alone')
            conds|= mode=='N' and q.cond in ('Link','LinkS','LinkT')
            if conds:
                corr[1]=1
            if not corr[0] and not self.logic.truth_check(info['truth'],q.truth):
                continue
            else:#if q.truth!='all':
                corr[0]=1
            candidates.append((txt,corr) )
        for c in candidates:
            if array(c[1]).all():
                return c
        for c in candidates:
            #if imperfect match, better choose a correct truth value
            #(it's easier to convert grammatical function)
            if c[1][0]:
                return c
        for c in candidates:
            if array(c[1]).any():
                return c
        try:
            return candidates[0]
        except:
            #unmarked case
            if mode =='S':
                return info['name'],[0,1]
            else:
                return info['name'],[0,1-mode_marked]

    def node_declaration(self,actor,info,**kwargs):
        text=''
        s,corr=self.node_say(actor,info)

        s= self.node_txtconvert(s,info,corr,mode='S')
        if 'hyperlink' in kwargs:
            if s[0]=='"':
                text+='"'
            text+='#r'+kwargs['hyperlink']+'#'
            if s[0]!='"':
                text+=s[:1]
            text+=s[1:]+ '##'
        else:
            text+=s
        return text



