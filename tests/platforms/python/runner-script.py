#!/usr/bin/env python3

import sys
import os
import traceback


def main():
    while True:
        path = sys.stdin.readline()[:-1]
        separator = sys.stdin.readline()[:-1]
        
        print(separator)
        
        pid = os.fork()
        
        if pid == 0:
            sys.path.append(os.path.dirname(path))
            with open(path) as source:
                try:
                    exec(source.read(), globals().copy())
                    return_code = 0
                except Exception:
                    traceback.print_exc()
                    return_code = 1
                
                print(separator)
                print(separator, file=sys.stderr)
                print(return_code)
                
                return
        else:
            os.waitpid(pid, 0)

main()
