from nose.tools import istest
import zuice

from nope.platforms.nodejs import NodeJs
from nope.platforms import nodejs
from nope import injection
from .. import execution
from .runner import SingleProcessRunner
from ...testing import wip



def _node_js_platform(optimise):
    bindings = injection.create_bindings()
    bindings.bind(nodejs.optimise).to_instance(optimise)
    return zuice.Injector(bindings).get(NodeJs)


@istest
class NodeJsExecutionTests(execution.ExecutionTests):
    platform = NodeJs
    
    @staticmethod
    def create_fast_runner():
        return SingleProcessRunner.start()
    
    test_getitem_dict = wip(execution.ExecutionTests.test_getitem_dict)
    test_unnested_list_comprehension = wip(execution.ExecutionTests.test_unnested_list_comprehension)

