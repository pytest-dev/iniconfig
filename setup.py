from setuptools import setup

# Ensures that setuptools_scm is installed, so wheels get proper versions
import setuptools_scm  # noqa


def local_scheme(version: object) -> str:
    """Skip the local version (eg. +xyz of 0.6.1.dev4+gdf99fe2)
    to be able to upload to Test PyPI"""
    return ""


setup(use_scm_version={"local_scheme": local_scheme})
