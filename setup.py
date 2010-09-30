"""
iniconfig: brain-dead simple config-ini parsing.

compatible CPython 2.3 through to CPython 3.2, Jython, PyPy

(c) 2010 Ronny Pfannschmidt, Holger Krekel
"""

import os, sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from iniconfig import __version__

def main():
    setup(
        name='iniconfig',
        py_modules=['iniconfig'],
        description=
        'iniconfig: brain-dead simple config-ini parsing',
        long_description = open('README.txt').read(),
        version= __version__,
        url='http://bitbucket.org/RonnyPfannschmidt/inipkg',
        license='MIT License',
        platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
        author='Ronny Pfannschmidt',
        author_email='Ronny.Pfannschmidt@gmx.de',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: POSIX',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: MacOS :: MacOS X',
            'Topic :: Software Development :: Libraries',
            'Topic :: Utilities',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3'],
    )

if __name__ == '__main__':
    main()
