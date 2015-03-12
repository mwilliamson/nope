#!/usr/bin/env python

import box
import box.wrapper

box.value[0] = box.value[0] + 1

print(box.value[0])
print(box.wrapper.value[0])

box.wrapper.value[0] = box.wrapper.value[0] + 1

print(box.value[0])
print(box.wrapper.value[0])
