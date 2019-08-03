"""Simple Cython package setup."""

from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension

source_files = [
    'lib.py',
    'libc.pyx',
    'libc.c',
]

extensions = [Extension("lib", source_files)]

setup(
    ext_modules=cythonize(extensions),
    version='0.0.1',
    name='speed_reader',
    maintainer='richimus123',
)
