### Program that applies a series of rules to update old maps saved as text.
# May break sometimes, but should save a LOT of effort for small changes (e.g. renaming)


## WIP!!!

fname=''

fin=open(fname,'r')
fout=open(fname+'~','w')

REPLACEMENT={
    '':''
    }

REM_ATTR={
    }

ADD_ATTR={
    }

new=[]
for line in fin:
    rep=line
    new.append(rep)
    
for n in new:
    fout.write(n)
