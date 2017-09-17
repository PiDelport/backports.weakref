# coding: utf-8
from setuptools import setup, find_packages


def README():
    with open('README.rst') as f:
        return f.read()


setup(
    name='backports.weakref',
    description="Backport of new features in Python's weakref module",
    long_description=README(),
    url='https://github.com/pjdelport/backports.weakref',

    author='Pi Delport',
    author_email='pjdelport@gmail.com',

    package_dir={'': 'src'},
    packages=find_packages('src'),

    setup_requires=['setuptools_scm'],
    use_scm_version=True,

    license='Python Software Foundation License',
    classifiers=[
        'Development Status :: 6 - Mature',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Python Software Foundation License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
