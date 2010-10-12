iniconfig: brain-dead simple parsing of ini files
=======================================================

iniconfig is a small and simple INI-file parser module
having a unique set of features:

* tested against Python2.4 across to Python3.2, Jython, PyPy
* maintains order of sections and entries
* supports multi-line values with or without line-continuations
* supports "#" comments everywhere
* raises errors with proper line-numbers
* no bells and whistles like automatic substitutions

If you encounter issues or have feature wishes please report them to:

    http://bitbucket.org/RonnyPfannschmidt/iniconfig/issues

Basic Example
===================================

>>> import iniconfig
>>> ...


Differences to configparser/ConfigParser
===============================================

- iniconfig does not allow two sections with the same name.
  it rathers throws an error instead of automatically merging.

- maintains order of sections

have fun,

Ronny and Holger

