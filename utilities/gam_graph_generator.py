# -*- coding: utf-8 -*-
from gam_graph import *
from gam_text import*
from gam_rules import *
from random import choice, shuffle, randint,uniform
from math import hypot,pi,atan2

def crossp(v,w):
    return v[0]*w[1]-w[0]*v[1]

def betavar(mean,stdev):
    nu= mean*(1-mean)/stdev**2 -1
    a=mean*nu
    b=(1-mean)*nu
    return rnd.betavariate(a,b)

class TraitGrammar(object):

    def __init__(self):
        self.trait_type={}

    def possible_links(self):
        pass

class StupidGrammar(TraitGrammar):
    #First example: police procedural generation
    patterns={
        ('person','loves','person'):
            {'genre':('Statement',),'role':'motive',
            },
        ('person','hates','person'):
            {'genre':('Statement',),'role':'motive',
            },
        ('person','is','person_attribute'):
            {'genre':('Statement','Speculation'),'role':'motive',
            },
        ('person','is','material_attribute'):
            {'genre':('Statement','Speculation'),'role':'context',
            },
        ('person','was in','place','time'):
            {'genre':('Narrative',),'role':'alibi',
            },
        ('person','has','item'):
            {'genre':('Statement','Speculation'),'role':'alibi',
            },
        ('item','is','material_attribute'):
            {'genre':('Statement','Speculation'),'role':'context',
            },
        ('I have','witness',"'s",'testimonial'):
            {'genre':('Narrative',),'role':'context',
            },
        }


    def __init__(self):
        super(StupidGrammar, self).__init__()
        types= ('item','place','person','time','witness', 'person_attribute','material_attribute')
        for i in types:
            f=fopen(database['basepath']+'gen/'+i+'.dat','r')
            traits=[]
            for j in f:
                traits.append(j.strip())
                self.trait_type[j.strip()]=i
                if len(traits)>6:
                    break
            setattr(self,i,traits)
        for patt in self.patterns:
            for c in patt:
                if not c in types:
                    self.trait_type[c]=c

    def make_goal(self):
        self.suspects=suspects=self.person[:]
        #culprit=choice(suspects)
        #suspects.remove(culprit)
        self.victim=victim=choice(suspects)
        suspects.remove(victim)
        self.murder_time=murder_time=choice(self.time)
        self.murder_place=murder_place=choice(self.place)
        self.murder_item=murder_item=choice(self.item)
        self.macguffin=macguffin=choice(self.item)

        goals=[]
        important=[]
        important.append( self.make_random([victim,macguffin]) )
        self.trait_type['innocent']='person_attribute'
        for s in suspects:
            goal=(s,'is','innocent'), 'Statement',2., 0.2, self.make_infos(str(s)+' is innocent')
            motive =self.make_random([s, choice([victim,macguffin]) ],subt=1,magn=4)
            alibi= self.make_random([s],role='alibi' ,subt=1,magn=4)
            important.append(alibi)
            important.append(motive)
            goals.append(goal)

        return goals, important


    def make_random(self,imposed=[],**opts):
        spat=self.patterns
        tt=self.trait_type

        subt=opts.get('subt',randint(0,3) )
        magn = opts.get('magn',randint(0,3) )
        subt= uniform( max(0.05,subt*.2-.5),.2+subt*.2)
        magn= uniform( max(0.5,magn*.3-.5),.5+magn*.3)

        patterns=spat.keys()[:]
        if 'role' in opts:
            if not hasattr(opts['role'],'__iter__'):
                opts['role']=opts['role'],
            patterns=[i for i in patterns if spat[i].get('role',None) in opts['role'] ]

        if imposed:
            for patt in tuple(patterns):
                impostypes=[tt[i] for i in imposed if i in tt]
                for c in patt:
                    if c in impostypes:
                        impostypes.remove(c)
                if impostypes: #not all imposed are found
                    patterns.remove(patt)

        if not patterns:
            raise Exception('Conditions impossible')

        patt=choice(patterns)
        genre=rnd.choice(spat[patt]['genre'])
        txt=''
        patt=list(patt)
        for i,c in enumerate(patt):
            if hasattr(self,c):
                patt[i]= rnd.choice(getattr(self,c)  )
            if c=='item':
                txt+='the '
            txt+=patt[i]+' '
        return patt, genre, magn, subt, self.make_infos(txt[:-1])

    def make_infos(self,label):
        infos={'name':label.capitalize(),#,'desc':label.capitalize(),
              #'quotes':'"'+label+'"'
                }
        return infos

    def link_from(self,pkg1):
        pass

    def link_between(self,pkg1,pkg2):
        spat=self.patterns
        tt=self.trait_type
        #print pkg1, pkg2
        pattern1,pattern2=[tt[i] for i in pkg1 if i in tt],[tt[i] for i in pkg2 if i in tt]
        #print pattern1,pattern2
        pattern1,pattern2=tuple(pattern1),tuple(pattern2)
        if 'innocent' in pattern1 and 'innocent' in pattern2:
            logic=(1,0)
            pattern='Deduction'
            magn=uniform(.2,.5)
            subt=uniform(0,.3)
        #elif pkg1[2]==pkg2[2] :
            #genre=(1,1)
        elif spat[pattern1]['role']=='alibi' and 'innocent' in pattern2:
            logic=(1,1)
            pattern='Deduction'
            magn=uniform(.2,.4)
            subt=uniform(0,.3)
        elif spat[pattern1]['role']=='motive'  and 'innocent' in pattern2:
            logic=(1,0)
            pattern='Deduction'
            magn=uniform(.2,.4)
            subt=uniform(0,.6)
        elif True in [c in pkg2 for c in pkg1 ]:
            pattern= 'Parallel'
            logic=(1,randint(0,1) )
            magn=uniform(.05,.25)
            subt=uniform(0.1,.8)
        elif pattern1==pattern2:
            pattern= 'Parallel'
            logic=choice( [(1,1), (0,0)])
            magn=uniform(.05,.25)
            subt=uniform(0.1,.9)
        else:
            logic=( randint(0,1), randint(0,1) )
            pattern='Context'
            magn=uniform(.05,.15)
            subt=uniform(0.4,1.0)
        if rnd.random()<0.2:
            logic+=1,
        else:
            logic+=0,
        if rnd.random()<0.05:
            logic+=1,
        else:
            logic+=0,
        #print logic
        return pattern,logic, magn,subt

    def make_random_link(self,traits1,traits2):
        possible=self.link_between(traits1,traits2)
        return rnd.choice(possible)


@extend(MatchGraph)
class MatchGraph:
    def make_new(self,props=None):
        if not props:
            props=self.Props()

        N=props.N
        k=props.k
        size=props.size
        genres=props.leading_genre,props.subleading_genre
        genre_fractions=props.genre_fractions


        doxa=int(round(N/10))  #base nodes on which everyone accords
        axioms=int(round(N/10)) #base nodes on which there can be discord
        return True


    def make(self,props=None):
        grammar=StupidGrammar()
        if props is None:
            props=self.Props()
        tt=grammar.trait_type
        tags={}
        goals,important=grammar.make_goal()
        textmaker=TextBase()
        nodes={}
        self.renew()
        self.pos={}

        N=props.N
        k=props.k
        size=props.size
        if props.grammar=='Default':
            G=netx.DiGraph()
            if N>1./k*3:
                G=netx.newman_watts_strogatz_graph(N, int(1./k), .1)
            else:
                for n in range(N):
                    G.add_node(n)
            for n in G.nodes():
                node=nodes[n]=self.Node()
                self.add(node)
                self.pos[node]=(randint(0,size[0]),randint(0,size[1]))
            for e in G.edges():
                n1,n2=e
                self.add(self.Link((nodes[n1],nodes[n2])))
            return


        margin=40
        npoles=1
        spring=1
        nback= max(len(important+goals)-1,N/3/npoles)
        maxd=hypot(*size)
        dist=ergonomy['canvas_typical_dist']

        #Backbone : low subtlety tree of nodes spanning the whole graph

        cpos=array(tuple(j/2 for j in size))
        G=netx.DiGraph()
        for p in range(npoles):
            G.add_node(p,assess=False,update=False)
            nodes[p]=self.Node()

            if npoles>1:
                theta=p*2*pi/npoles
                pos = cpos+ array( (cos(theta),sin(theta) )) *dist*2
            else :
                pos = cpos
            self.pos[p]=pos

            pred=[p]
            for t in range(nback):

                idt=npoles+p*nback+t
                nodes[idt]=self.Node()
                G.add_node(idt,assess=False,update=False)

                pr=rnd.choice(pred)
                G.add_edge(pr,idt)
                pred.append(idt)
        ang={}
        for n in nodes:
            free=G.successors(n)
            if not free:
                continue
            fixed=G.predecessors(n)
            if not fixed:
                angles=[]
            else:
                angles=[(ang[(s,n)]+pi)%(2*pi) for s in fixed]
            nei = len(free)+len(fixed)

            potangles=[2*pi/nei * z for z in range(nei)]

            if fixed:
                ref=sum(angles)/len(angles)
                potangles=[(i+ref+2*pi)%(2*pi) for i in potangles]
                dists=[min( (ang1-ang2+2*pi)%(2*pi) for ang2 in angles) for ang1 in potangles]
                potangles=sorted(potangles,key=lambda e:dists[potangles.index(e)])
                for z in range(len(fixed)):
                    potangles.pop(0)
            for theta in potangles:
                nxt=free.pop(0)
                var=.5/len(potangles)
                theta+=uniform(-var,var)
                self.pos[nxt]=self.pos[n] +array( (cos(theta),sin(theta) )) *2*dist*uniform(.8,1.2)
                ang[(n,nxt)]=theta

        print 'Supplementary nodes'
        #Bonus :
        close={}
        for n in range(max(nodes.keys())+1,N):
            dists=[]
            tim=pg.time.get_ticks()
            while not dists:
                close[n]=[]
                pos=array( (uniform(margin,size[0]-margin),uniform(margin,size[1]-margin)))
                for s in nodes:
                    test=hypot(*(pos-self.pos[s]))
                    if test<2*dist:
                        close[n].append( s)
                        dists.append(test)

            while min(dists)<dist*.8:
                scl=close[n][dists.index(min(dists))]
                pos += (pos-self.pos[scl])*.2 + array( (uniform(-.1,.1),uniform(-.1,.1)) )*dist
                dists=[]
                for s in close[n]:
                    dists.append(hypot(*(pos-self.pos[s])))
                if pg.time.get_ticks()-tim>10:
                    break
            self.pos[n]=pos
            dists=[]
            nods=nodes.keys()
            for s in nods:
                dists.append(hypot(*(pos-self.pos[s])))
            nods=sorted(nods,key = lambda e: dists[nods.index(e)] )
            G.add_node(n,assess=False,update=False)
            G.add_edge(nods[0],n)
            if uniform(0,1)<.4:
                G.add_edge(rnd.choice(nods[1:3]),n)
            #print min(dists),hypot(*(pos-self.pos[scl])),len(nods),scl,n,self.pos[scl],self.pos[n]



        print 'Decorating'
        for n in G.nodes():
            nodes[n]=self.Node()
            self.add(nodes[n])

        print 'Edges'
        #Edges
        for e in G.edges():
            n1,n2=e[0],e[1]
            unfixed=[ n for n in e if not n in tags]

            while unfixed:
                n=unfixed.pop(-1)
                if len(unfixed)==1:
                    fixed=n
                    try:
                        tags[n]=(goals+important).pop(0)
                    except:
                        tags[n]= grammar.make_random()
                else:
                    fixed=[ w for w in e if not w in unfixed and w!= n][0]
                    best=(0,0)
                    for g in goals+important:
                        pattern,logic, magn,subt=grammar.link_between(tags[fixed],g[0])
                        if magn>best[0]:
                            best=(magn,g)
                    if best[0]!=0:
                        tags[n]=g
                        if g in goals:
                            goals.remove(g)
                        else :
                            important.remove(g)
                    else:
                        elems=[i for i in tags[fixed] if i in tt and tt[i]!=i]
                        imposed=choice(elems)
                        tags[n]=grammar.make_random(imposed )
                tags[n], genre, magn, subt, infos=tags[n]
                #print 'tagged', n,tags[n]
                effnumber=rint(betavar(.4,.4)*2*(subt+magn) )
                effects=[]
                for eff in range(effnumber):
                    efinf={'val':betavar(.5+subt/20.,.05+subt/20.),
                        'res':('face','terr','path')[randint(0,2)],
                        'target':('claimer','hearer')[randint(0,1)]}
                    if efinf['res']=='path':
                        efinf['val']=rfloat(efinf['val'])/2-.2
                        efinf['target']='claimer'
                    else:
                        efinf['val']=rfloat(efinf['val']-.5)
                    if abs(efinf['val'])>.01:
                        effects.append(EthosEffect(name=textmaker.ethos_effect_name(efinf),**efinf))
                infos.update({'val':magn,'subt':subt,'genre':genre,'effects':effects}
                    )
                for i,j in infos.iteritems():
                    self.set_info(nodes[n],i,j)

            pattern,logic, magn,subt=grammar.link_between(tags[n1],tags[n2])
            infos=textmaker.link_text_generator(pattern,magn,[self.get_info(nodes[n],'genre') for n in (n1,n2) ])
            self.add(self.Link((nodes[n1],nodes[n2])),val=magn,logic=logic,subt=subt,pattern=pattern,**infos)
        for i, j in self.pos.iteritems():
            self.pos[i]=array( [int(x) for x in self.pos[i]] )

        if not spring :
            self.pos=dict( (self.nodes[i],self.pos[i]) for i in sorted( self.pos) )
            return True

        self.pos=dict([ (self.nodes[i],[margin+int(k*s) for k,s in zip(list(j),size)])
            for i,j in netx.spring_layout(G,2,self.pos,None,100).iteritems()])

        return













