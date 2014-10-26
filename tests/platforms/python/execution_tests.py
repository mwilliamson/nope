from nose.tools import istest

from nope.platforms import python
from .. import execution


@istest
class Python3ExecutionTests(execution.ExecutionTests):
    platform = python.Python3
    runner = execution.SubprocessRunner("python3.4")
