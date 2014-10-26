import os
import signal

import spur
import requests

from ...retry import retry
from ..execution import SubprocessRunner


def start_runner():
    fast_test = os.environ.get("TEST_FAST")
    if fast_test:
        return SingleProcessRunner.start()
    else:
        return SubprocessRunner("node")


class SingleProcessRunner(object):
    @staticmethod
    def start():
        local = spur.LocalShell()
        port = 8112
        url = "http://localhost:{}".format(port)
        runner_path = os.path.join(os.path.dirname(__file__), "runner/runner.js")
        process = local.spawn(
            ["node", runner_path, str(port)],
            allow_error=True,
        )
        
        retry(lambda: requests.get(url + "/heartbeat"), ConnectionError)
        return SingleProcessRunner(process, url)
    
    def __init__(self, process, url):
        self._process = process
        self._url = url
    
    def run(self, cwd, main, allow_error):
        response = requests.post(self._url, data={"cwd": cwd, "main": main})
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
    
    def stop(self):
        self._process.send_signal(signal.SIGINT)
        self._process.wait_for_result()


class ExecutionResult(object):
    def __init__(self, return_code, output, stderr_output):
        self.return_code = return_code
        self.output = output
        self.stderr_output = stderr_output
