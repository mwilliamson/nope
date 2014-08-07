from nose.tools import istest

from nope.platforms import python
from .. import execution


@istest
class Python2ExecutionTests(execution.ExecutionTests):
    platform = python.Python2()


@istest
class Python3ExecutionTests(execution.ExecutionTests):
    platform = python.Python3()
