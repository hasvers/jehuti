import os,re


for f in os.listdir("./"):
    if '.arc.txt' in f:
        inf= open(f,"r")
        ouf=open(f.replace('.arc.txt','')+'.htm',"w")
        ouf.write('<html><title>{}</title><body>'.format(f.replace('.arc.txt','')))
        for l in inf:
            pats=[p for p in re.findall("#.*?#",l) if p!='##']
            if len(pats)==1 and pats[0]==l.strip():
                 l=l.replace(p,'<a name="{}">{}</a>'.format(p.replace('#',''),p))   
            else:
                for p in pats:
                    l=l.replace(p,'<a href="#{}">{}</a>'.format(p.replace('#',''),p))   
            ouf.write(l+'<br>')            
        ouf.write('</body></html>')
        inf.close()
        ouf.close()
