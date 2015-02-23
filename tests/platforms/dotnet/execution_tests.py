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
    
    can_import_local_module = wip(execution.ExecutionTests.can_import_local_module)
    can_import_local_package = wip(execution.ExecutionTests.can_import_local_package)
    can_import_module_in_package = wip(execution.ExecutionTests.can_import_module_in_package)
    can_import_module_in_package_using_import_from = wip(execution.ExecutionTests.can_import_module_in_package_using_import_from)
    can_import_value_from_local_package = wip(execution.ExecutionTests.can_import_value_from_local_package)
    test_getitem_dict = wip(execution.ExecutionTests.test_getitem_dict)
    test_import_of_module_in_standard_library = wip(execution.ExecutionTests.test_import_of_module_in_standard_library)
    test_in_operator_list = wip(execution.ExecutionTests.test_in_operator_list)
    test_transformer_for_collections_namedtuple = wip(execution.ExecutionTests.test_transformer_for_collections_namedtuple)
    test_unnested_generator_expression = wip(execution.ExecutionTests.test_unnested_generator_expression)
    test_unnested_list_comprehension = wip(execution.ExecutionTests.test_unnested_list_comprehension)
