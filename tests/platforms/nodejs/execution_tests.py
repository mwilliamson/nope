import os

import tempman
from nose.tools import istest, assert_not_equal

import nope
from nope.platforms.nodejs import NodeJs
from nope.platforms import nodejs
from .. import execution


# TODO:
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
            
        nope.compile(source_dir, optimised_dest_dir, _optimised_node_js)
        nope.compile(source_dir, unoptimised_dest_dir, _unoptimised_node_js)
        
        def read(path):
            with open(path) as file_:
                return file_.read()
        
        assert_not_equal(
            read(os.path.join(optimised_dest_dir, "main.js")),
            read(os.path.join(unoptimised_dest_dir, "main.js")),
        )


@istest
class NodeJsExecutionTests(execution.ExecutionTests):
    platform = NodeJs
    
    @staticmethod
    def create_bindings(bindings):
        bindings.bind(nodejs.optimise).to_instance(True)
    
    test_getitem_dict = None
    test_slice_list = None
    test_unnested_list_comprehension = None
    test_unnested_generator_expression = None


@istest
class UnoptimisedNodeJsExecutionTests(execution.ExecutionTests):
    platform = NodeJs
    
    @staticmethod
    def create_bindings(bindings):
        bindings.bind(nodejs.optimise).to_instance(False)
    
    test_getitem_dict = None
    test_slice_list = None
    test_unnested_list_comprehension = None
    test_unnested_generator_expression = None
