import os
import uuid
import signal

import subprocess


class SingleProcessRunner(object):
    @staticmethod
    def start(platform):
        runner_path = os.path.join(os.path.dirname(__file__), "runner-script.py")
        process = subprocess.Popen(
            ["python3", "-u", runner_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        
        return SingleProcessRunner(process)
    
    def __init__(self, process):
        self._process = process
    
    def run(self, cwd, main, allow_error):
        separator = str(uuid.uuid4()).encode("utf8")
        
        self._process.stdin.write(os.path.join(cwd, main).encode("utf8"))
        self._process.stdin.write(b"\n")
        self._process.stdin.write(separator)
        self._process.stdin.write(b"\n")
        self._process.stdin.flush()
        
        line = self._process.stdout.readline()[:-1]
        assert line == separator, line
        
        stdout = self._read_until_separator(self._process.stdout, separator)
        return_code = int(self._process.stdout.readline())
        stderr = self._read_until_separator(self._process.stderr, separator)
        
        result = ExecutionResult(return_code, stdout, stderr)
        
        if allow_error or result.return_code == 0:
            return result
        else:
            raise ValueError("return code was {}\nstdout:\n{}\n\nstderr:\n{}".format(
                result.return_code, result.output, result.stderr_output
            ))
    
    def _read_until_separator(self, fileobj, separator):
        output = []
        
        while True:
            line = fileobj.readline()
            if line[:-1] == separator:
                return b"".join(output)
            else:
                output.append(line)
    
    def stop(self):
        self._process.send_signal(signal.SIGINT)
        self._process.wait()


class ExecutionResult(object):
    def __init__(self, return_code, output, stderr_output):
        self.return_code = return_code
        self.output = output
        self.stderr_output = stderr_output
