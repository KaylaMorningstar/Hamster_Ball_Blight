# cd C:\Users\Kayle\Desktop\HBB\CURRENT
# py -3 cython_setup.py build_ext --build-lib "C:\Users\Kayle\Desktop\HBB\CURRENT\Code\Cython" --force
from os import getcwd
from glob import glob
from distutils.core import setup
from Cython.Build import cythonize

# turn on annotations
import Cython.Compiler.Options
Cython.Compiler.Options.annotate = True

for cython_file in glob(f"{getcwd()}\\Code\\Cython\\*.pyx"):
    try:
        setup(ext_modules=cythonize(cython_file, build_dir="build", annotate=True))
    except:
        continue
