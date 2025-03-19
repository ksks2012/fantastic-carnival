#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup  # pylint: disable=import-error
from setuptools import find_packages

setup(name="fantastic-carnival",
		version="0.0.1",
		description="",
		packages=find_packages(),
		install_requires=[
			"beautifulsoup4>=4.13.3,<4.14.0",
            "PyYaml >= 6.0, < 7.0",
		],
		entry_points={
		},
		classifiers=[
				"Development Status :: 3 - Alpha",
				"Intended Audience :: Developers",
				"Operating System :: POSIX",
				"Programming Language :: Python :: 3.12.3",
		],
		)

# vim: tabstop=4 shiftwidth=4
