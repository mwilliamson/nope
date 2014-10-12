#!/usr/bin/env python

import messages.hello

#:: str -> none
def say(value):
    print(value)

say(messages.hello.value)
