#!/usr/bin/env python

import box as x
import box as y

x.value[0] = x.value[0] + 1

print(x.value[0])
print(y.value[0])

y.value[0] = y.value[0] + 1

print(x.value[0])
print(y.value[0])
