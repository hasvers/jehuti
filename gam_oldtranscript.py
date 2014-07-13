# -*- coding: utf-8 -*-

class Transcripter(object):

    def make_transcript(self,batch,match_handler,pov, evt=None):
        #transcript is made from the point of view of pov player
        match=match_handler.data
        cast=match.cast
        text=TextMaker(match)

        #TODO in future versions, more clever transcripting than just concatenation of individual events
        if not evt :
            #print batch.events, '||||',batch.root_events
            transcript=''
            #print [(e.type,e.item,e.actor) for e in batch.root_events]
            for e in batch.root_events:
                if True in tuple(x  in e.type for x in ('claim',)):#'reac', 'interpret')):
                    if transcript:
                        transcript+='\r'
                    transcript+= self.make_transcript(batch,match_handler,pov,e)
                #except:
                #    print 'non transcriptable', e

            transcript+=self.reac_transcript( match,[e for e in batch.events if 'reac' in e.type and e.actor==pov],pov)
            transcript+=self.reac_transcript(match, [ e for e in batch.events if 'interp' in e.type and e.actor==pov],pov,'interp')
            #After the root_events, look for children events that may contain autonomous info

            for e in batch.events:
                if 'concede' in e.type :
                    transcript += cast.get_info(e.actor,'name')+ ' concedes the point to '
                    transcript+=cast.get_info(e.receiver,'name')+'.\r'

            if not transcript:
                if batch.actor != pov:
                    txt=cast.get_info(batch.actor,'name')+ ' is lost in thought.'
                else :
                    txt='You let your mind run free.'
                    newarg=[j for e in batch.events if 'expl' in e.type
                     for j in e.states.node[e.state]['children_states'] if
                      j.state==e.states.node[e.state]['children_states'][j] ]
                    if len(newarg)>1 :
                        txt+=' New ideas float to the surface.'
                    elif newarg:
                        txt+=' A new idea floats to the surface.'
                transcript +=txt


            if not hasattr(batch,'effects'):
                return transcript

            #TODO: This part will be replaced by emotes
            for tgt,eff in batch.effects.iteritems():
                color=graphic_chart['text_color_positive']
                if hasattr(eff,'keys'):
                    effs=''
                    for i,j in eff.iteritems():
                        if j<0:
                            effs+= str(i) + ' -'#+ str(int(round(j* database['floatprecision'])))
                            color=graphic_chart['text_color_negative']
                        else:
                            effs+= str(i) + ' +'#+ str(int(round(j* database['floatprecision'])))
                    eff=effs
                else:
                    effs=str(int(round(eff* database['floatprecision'])))
                    if eff<0:
                        color=graphic_chart['text_color_negative']
                        eff='-'#effs
                    else:
                        eff='+'#+effs

                transcript +='\n #c'+str(color)+'#'+match.cast.get_info(tgt[0],'name')+' '+str(tgt[1]) +' '+str(eff)+'##'
            return transcript

        transcript=''
        if 'claim' in evt.type:
            item=evt.item
            act=evt.actor
            iti = match.actorgraph[act].get_info(item)
            acti = match.cast.get_info(act)
            if item.type=='node':
                hyper='("'+iti['name']+'",['+ str(item.ID)
                hyper+= '],{"affects":user.ui.scene.canvas.graph})'
                transcript+=text.node_declaration(acti,iti,intro=True,conclude=True,hyperlink=hyper)
                for c in batch.child_events.get(evt,[]) +  batch.child_events.get(evt.decl,[]):
                    #print 'transcripting', c, c.actor, c.item
                    transcript+=self.make_transcript(batch,match_handler,pov,c)
            if item.type=='link':
                p1,p2= item.parents
                ninfo1,ninfo2=None,None
                #TODO : This will be a problem because currently only CLaimEvt has children for required items
                #if p1 in [e.item for e in batch.child_events[evt] if e.type==evt.type ]:
                ninfo1=match.actorgraph[act].get_info(p1)
                #if p2 in [e.item for e in batch.child_events[evt] if e.type==evt.type]:
                ninfo2=match.actorgraph[act].get_info(p2)
                hyper1='("'+ninfo1['name']+'",['+ str(p1.ID)
                hyper1+= '],{"affects":user.ui.scene.canvas.graph})'
                hyper2='("'+ninfo2['name']+'",['+ str(p2.ID)
                hyper2+= '],{"affects":user.ui.scene.canvas.graph})'
                transcript+=text.link_declaration(acti,ninfo1,ninfo2,iti,hyper1=hyper1,hyper2=hyper2)
                for c in batch.child_events.get(evt,[]) +  batch.child_events.get(evt.decl,[]):
                    if c.item==evt.item:
                        #print 'transcripting', c, c.actor, c.item
                        transcript+=self.make_transcript(batch,match_handler,pov,c)

        if 'react' in evt.type:
            if evt.state==0:
                print 'gamtext: Wut react state 0', evt, evt.actor
                return transcript
            act=evt.actor
            sinf = match.cast.get_info(act)
            agreement=evt.kwargs['agreement']
            if evt.is_discovery:
                transcript += text.convincing_reaction(sinf,agreement)
            else :
                transcript += text.agreement_reaction(sinf,agreement)
        if 'interpret' in evt.type:
            #TODO: change this (right now transcript of the reaction rather than its interpretation)
            return self.make_transcript(batch,match_handler,pov,evt.parent)
        return transcript

    def cluster_evts(evts):
        cls={}
        for e in evts:
            cls[e.item].setdefault([])
            cls[e.item].append(e)
        return cls
        #What is below is perhaps not clever
        for i,c in tuple(cls.iteritems()):
            #if not i in cls:
                #continue
            for j,c in tuple(cls.iteritems()):
                #if not j in cls:
                    #continue
                if j in i.required:
                    cls[i]+=cls[j]
                    #del cls[j]

    def reac_transcript(self,match,evts,pov,mode='reac'):
        return ''
        if not evts:
            return ''
        txt=''
        if mode =='reac':
            dic={(1,0):'agree with',(0,0):'disagree with',
                (1,1):'are convinced by',(0,1):'are unconvinced by',1:'and',0:'but' }
        else:
           dic={(1,0):'agrees with',(0,0):'disagrees with',
                (1,1):'seems convinced by',(0,1):'seems unconvinced by',1:'and',0:'but' }
        cls=self.cluster_evts(evts)
        totagr=lambda e:sum(j.kwargs['agreement'] for j in e)
        inf=match.cast.get_info
        for i,c in cls.iteritems():
            if i.type=='link':
                premise=totagr(cls[i.parents[0]])
                pdis=array([e.is_discovery for e in cls[i.parents[0]]]).any()
                concl=totagr(cls[i.parents[1]])
                cdis=array([e.is_discovery for e in cls[i.parents[1]]]).any()
                if mode=='reac':
                    pronoun='You'
                else:
                    pronoun=inf(pov,'name')
                txt+='{} {} the premise {} {} the conclusion.'.format(pronoun,
                    dic[(premise>0,pdis) ],dic[premise==concl],dic[(concl>0,cdis) ])
            if i.type=='node':
                dis=array([e.is_discovery for e in cls[i]]).any()
                if dis:
                    transcript += text.convincing_reaction(inf(pov),agreement)
                else:
                    transcript += text.agreement_reaction(inf(pov),agreement)
            else :
                transcript += text.agreement_reaction(sinf,agreement)
        return txt