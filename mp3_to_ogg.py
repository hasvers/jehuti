#Using sox, convert all mp3s found in subfolders into oggs
import os

myfiles=  [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser("./")) for f in fn]

for i in myfiles:
    if '.mp3' in i:
        os.popen2('sox {} {}'.format(i,i.replace('mp3','ogg')))
