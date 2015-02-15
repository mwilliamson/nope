import os

import tempman
from nose.tools import istest

from nope.platforms.dotnet import DotNet
from .. import execution
from ...testing import wip


@istest
class DotNetExecutionTests(execution.ExecutionTests):
    platform = DotNet
    

def _skip_tests():
    for attr_name in dir(DotNetExecutionTests):
        attr = getattr(DotNetExecutionTests, attr_name)
        if getattr(attr, "__test__", False):
            setattr(DotNetExecutionTests, attr_name, wip(attr))
    
_skip_tests()
