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
    
    importing_same_module_with_absolute_and_relative_import_returns_same_module = wip(execution.ExecutionTests.importing_same_module_with_absolute_and_relative_import_returns_same_module)
    
    test_getitem_dict = wip(execution.ExecutionTests.test_getitem_dict)
    test_in_operator_list = wip(execution.ExecutionTests.test_in_operator_list)
    test_unnested_generator_expression = wip(execution.ExecutionTests.test_unnested_generator_expression)
    test_unnested_list_comprehension = wip(execution.ExecutionTests.test_unnested_list_comprehension)
