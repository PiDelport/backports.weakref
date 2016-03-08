============================
Working on backports.weakref
============================


Running the tests
=================

Running ``tox``, ``detox``, or ``pytest`` should all work.

With ``unittest``::

    python -m unittest discover tests


Coverage
========

With ``coverage``::

    coverage run -m unittest discover tests
    coverage report
    coverage html

With ``pytest`` and ``pytest-cov``::

    py.test --cov
    py.test --cov --cov-report=html

