from nose.tools import istest

from nope.platforms.nodejs import NodeJs
from .. import execution


@istest
class NodeJsExecutionTests(execution.ExecutionTests):
    platform = NodeJs()
    
    test_while = None
