# -*- coding: utf-8 -*-
import os, sys, re
from pathlib import Path

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

incGlob = os.environ.get('TT_CYINC', '*.py')
excGlob = os.environ.get('TT_CYEXC', 'setup.py main.py')

print('setup.py: TT_CYINC=' + incGlob)
print('setup.py: TT_CYEXC=' + excGlob)
root = Path('.')
includes = {f for glob in re.split(r'\s+', incGlob) for f in root.glob(glob)}
excludes = {f for glob in re.split(r'\s+', excGlob) for f in root.glob(glob)}
includes -= excludes

_ext = lambda wp: Extension('.'.join([*wp.parts[0:-1], os.path.splitext(wp.parts[-1])[0]]), [str(wp)])
extensions = [_ext(f) for f in includes]

# extensions = [
#     Extension("testproject.my1", ["testproject/my1.py"]),
#     Extension("testproject.my3", ["testproject/my3.py"]),
# ]
setup(
    name="fuzz",
    ext_modules = cythonize(extensions, language_level="3")
)

# 如果指定了TT_DELETE_SOURCE环境变量，则删除生成的 .c 和 .py 源文件
if os.environ.get('TT_DELETE_SOURCE') == "1":
    print('setup.py: 删除C文件和PY源文件：')
    for f in includes:
        f = f.resolve()
        cpath = os.path.join(f.parts[0], *f.parts[1:-1], os.path.splitext(f.parts[-1])[0] + '.c')
        if os.path.exists(cpath):
            os.remove(cpath)
            print('> ' + cpath)
        if os.path.exists(str(f)):
            os.remove(str(f))
            print('> ' + str(f))
