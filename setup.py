#!/usr/bin/env python
# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="quickmvc",
    version="0.1.3",
    keywords=["quickpython-mvc", "quickpython", "quick", "WEB", "database", "MVC"],  # 关键字
    description="Python rapid development framework .",
    long_description="Python rapid development framework ",
    license="MIT Licence",

    url="https://github.com/quickpython",
    author="lo106258",
    author_email="lo106258@gmail.com",

    packages=find_packages(),
    include_package_data=True,
    scripts=['./boot.py', './config.py', './README.md', './requirements.txt'],
    platforms="any",
    install_requires=["tornado", "pymysql"],
    extras_require={':python_version <= "3.6"': ['enum34', 'future']}
)
