#!/usr/bin/env python
#from setuptools import setup
### dummy touch
from distutils.core import setup
import os,glob,sys
assert sys.version_info >= (3,6),('Requires python>=3.6, found python==%s'%('.'.join([str(x) for x in sys.version_info[:3]])))

config = dict(
	name='metacsv_ath_rnaseq',
	version = '0.0.1',
	packages=['metacsv_ath_rnaseq'],
	python_requires = ">= 3.6",
	license='MIT',
	author='Feng Geng',
	author_email='shouldsee.gem@gmail.com',
	classifiers = [
	'Programming Language :: Python :: 3.6',
	'Programming Language :: Python :: 3.7',
	],
	install_requires=open('requirements.txt','r').read().splitlines(),
)
setup(**config)