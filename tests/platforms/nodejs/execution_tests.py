import os

import tempman
from nose.tools import istest, assert_not_equal
import zuice

import nope
from nope.platforms.nodejs import NodeJs
from nope.platforms import nodejs
from nope import injection
from .. import execution
from .runner import SingleProcessRunner
from ...testing import wip


# TODO: remove if unnecessary
#~ @istest
def sanity_check_optimised_and_unoptimised_compilers_produce_different_output():
    with tempman.create_temp_dir() as temp_dir:
        source_dir = os.path.join(temp_dir.path, "src")
        optimised_dest_dir = os.path.join(temp_dir.path, "optimised")
        unoptimised_dest_dir = os.path.join(temp_dir.path, "unoptimised")
        
        os.mkdir(source_dir)
        os.mkdir(optimised_dest_dir)
        os.mkdir(unoptimised_dest_dir)
        
        with open(os.path.join(source_dir, "main.py"), "w") as main_file:
            main_file.write("#!/usr/bin/env python\n")
            main_file.write("print(1 + 1)")
            
        nope.compile(source_dir, optimised_dest_dir, _node_js_platform(optimise=True))
        nope.compile(source_dir, unoptimised_dest_dir, _node_js_platform(optimise=False))
        
        def read(path):
            with open(path) as file_:
                return file_.read()
        
        assert_not_equal(
            read(os.path.join(optimised_dest_dir, "main.js")),
            read(os.path.join(unoptimised_dest_dir, "main.js")),
        )


def _node_js_platform(optimise):
    bindings = injection.create_bindings()
    bindings.bind(nodejs.optimise).to_instance(optimise)
    return zuice.Injector(bindings).get(NodeJs)


class NodeJsExecutionTests(execution.ExecutionTests):
    platform = NodeJs
    
    @staticmethod
    def create_fast_runner():
        return SingleProcessRunner.start()
    
    test_getitem_dict = wip(execution.ExecutionTests.test_getitem_dict)
    test_unnested_list_comprehension = wip(execution.ExecutionTests.test_unnested_list_comprehension)
    test_unnested_generator_expression = wip(execution.ExecutionTests.test_unnested_generator_expression)


@istest
class OptimisedNodeJsExecutionTests(NodeJsExecutionTests):
    @staticmethod
    def create_bindings(bindings):
        bindings.bind(nodejs.optimise).to_instance(True)


# TODO: remove if unnecessary
#~ @istest
#~ class UnoptimisedNodeJsExecutionTests(NodeJsExecutionTests):
    #~ @staticmethod
    #~ def create_bindings(bindings):
        #~ bindings.bind(nodejs.optimise).to_instance(False)
