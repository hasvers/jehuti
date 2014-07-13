# -*- mode: python -*-
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
             pathex=['/home/neve/Projects/Jeu'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
inifiles = Datafiles('database.ini', 'graphic_chart.ini','ergonomy.ini', strip_path=False)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          inifiles,
          name='__main__',
          debug=False,
          strip=None,
          upx=True,
          console=True )
