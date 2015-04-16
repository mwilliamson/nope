import os

import tempman
from nose.tools import istest

from nope.platforms.dotnet import DotNet
from .. import execution
#from ...testing import wip
def wip(*args):
    return None

@istest
class DotNetExecutionTests(execution.ExecutionTests):
    platform = DotNet
    
    test_getitem_dict = wip(execution.ExecutionTests.test_getitem_dict)
    test_in_operator_list = wip(execution.ExecutionTests.test_in_operator_list)
