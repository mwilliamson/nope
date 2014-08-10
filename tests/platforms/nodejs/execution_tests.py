from nose.tools import istest

from nope.platforms.nodejs import NodeJs
from .. import execution


@istest
class NodeJsExecutionTests(execution.ExecutionTests):
    platform = NodeJs()
    
    # TODO: enable this test
    fib_program_prints_result_to_stdout = None
