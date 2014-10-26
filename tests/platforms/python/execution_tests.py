from nose.tools import istest

from nope.platforms import python
from .. import execution
from .runner import SingleProcessRunner


@istest
class Python3ExecutionTests(execution.ExecutionTests):
    platform = python.Python3
    
    @classmethod
    def create_fast_runner(cls):
        return SingleProcessRunner.start(cls.platform)
