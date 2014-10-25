import os
import signal

import tempman
from nose.tools import istest, assert_not_equal
import zuice
import spur
import requests

import nope
from nope.platforms.nodejs import NodeJs
from nope.platforms import nodejs
from nope import injection
from .. import execution


_fast_test = os.environ.get("TEST_FAST")

if _fast_test:
    _runner = [None]
    _port = 8112

    def setup_module():
        local = spur.LocalShell()
        runner_path = os.path.join(os.path.dirname(__file__), "runner/runner.js")
        _runner[0] = local.spawn(
            ["node", runner_path, str(_port)],
            allow_error=True,
        )
        # TODO: implement proper retry
        import time
        time.sleep(0.1)
        
    def teardown_module():
        _runner[0].send_signal(signal.SIGINT)
        _runner[0].wait_for_result()


@istest
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
    
    test_getitem_dict = None
    test_slice_list = None
    test_unnested_list_comprehension = None
    test_unnested_generator_expression = None
    
    if _fast_test:
        def run(self, platform, cwd, main, allow_error):
            
            url = "http://localhost:{}".format(_port)
            response = requests.post(url, data={"cwd": cwd, "main": main})
            response_body = response.json()
            result = ExecutionResult(
                int(response_body["returnCode"]),
                response_body["stdout"].encode("utf8"),
                response_body["stderr"].encode("utf8"),
            )
            if allow_error or result.return_code == 0:
                return result
            else:
                raise ValueError("return code was {}\nstdout:\n{}\n\nstderr:\n{}".format(
                    result.return_code, result.output, result.stderr_output
                ))


class ExecutionResult(object):
    def __init__(self, return_code, output, stderr_output):
        self.return_code = return_code
        self.output = output
        self.stderr_output = stderr_output


@istest
class OptimisedNodeJsExecutionTests(NodeJsExecutionTests):
    @staticmethod
    def create_bindings(bindings):
        bindings.bind(nodejs.optimise).to_instance(True)


@istest
class UnoptimisedNodeJsExecutionTests(NodeJsExecutionTests):
    @staticmethod
    def create_bindings(bindings):
        bindings.bind(nodejs.optimise).to_instance(False)
