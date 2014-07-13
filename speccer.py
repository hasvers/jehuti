import os
try:
    fin=open("./__main__.spec",'r')
    fout=open("./__main__.spec.arc",'w')
    for l in fin:
        fout.write(l)
    fin.close()
    fout.close()
except:
    print 'No previous'

fout=open("./__main__.spec",'w')

myfiles= ['"{}"'.format(i) for i in [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser("./")) for f in fn] if
          not '~' in i and not '/build' in i and not '/dist' in i and not '.spec' in i and not '.py' in i and not '__main__' in i
          and not 'pyinstaller' in i and not './doc' in i and not '.db' in i and not 'notempty' in i]

inifile=[]
inidef=''
plusallfiles=''
nn=0
while myfiles :
    nn+=1
    inifile.append('inifile{}'.format(nn) )
    locus=[]
    for x in range(min(20,len(myfiles))):
        locus.append(myfiles.pop(0))
    inidef+='{}  = Datafiles({}, strip_path=False)\n'.format(inifile[-1],','.join(locus))
    plusallfiles += ', {}'.format(inifile[-1] )

spec='''# -*- mode: python -*-
def Datafiles(*filenames, **kw):
    import os
    
    def datafile(path, strip_path=True):
        parts = path.split('/')
        path = name = os.path.join(*parts)
        if strip_path:
            name = os.path.basename(path)
        return name, path, 'DATA'

    strip_path = kw.get('strip_path', True)
    return TOC(
        datafile(filename, strip_path=strip_path)
        for filename in filenames
        if os.path.isfile(filename))

a = Analysis(['__main__.py'],
             pathex=['C:\To_build\'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)

{}

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='__main__.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )

coll =COLLECT(exe,
          a.binaries,
          a.zipfiles,
          a.datas{},
          strip=None,
          upx=True,    
          name='collected',    
          '''.format(inidef,plusallfiles)
fout.write(spec)
fout.close()
