"""
iniconfig: brain-dead simple config-ini parsing.

compatible CPython 2.3 through to CPython 3.2, Jython, PyPy

(c) 2010 Ronny Pfannschmidt, Holger Krekel
"""

from setuptools import setup


def main():
    setup(
        packages=["iniconfig"],
        package_dir={"": "src"},
        use_scm_version=True,
        url="http://github.com/RonnyPfannschmidt/iniconfig",
        include_package_data=True,
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
