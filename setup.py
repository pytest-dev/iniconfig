"""
iniconfig: brain-dead simple config-ini parsing.

compatible CPython 2.3 through to CPython 3.2, Jython, PyPy

(c) 2010 Ronny Pfannschmidt, Holger Krekel
"""

from setuptools import setup


def main():
    setup(
        packages=['iniconfig'],
        package_dir={'': 'src'},
        description='iniconfig: brain-dead simple config-ini parsing',
        
        use_scm_version=True,
        url='http://github.com/RonnyPfannschmidt/iniconfig',
        license='MIT License',
        platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
        author='Ronny Pfannschmidt, Holger Krekel',
        author_email=(
            'opensource@ronnypfannschmidt.de, holger.krekel@gmail.com'),
        include_package_data=True,
        zip_safe=False,
    )

if __name__ == '__main__':
    main()
