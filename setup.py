#!/usr/bin/env python

from setuptools import setup

if __name__ == "__main__":
    use_scm = {"write_to": "organelle_segmenter_plugin/_version.py"}
    setup(use_scm_version=use_scm)


    