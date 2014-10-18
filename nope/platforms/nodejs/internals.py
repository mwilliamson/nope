from . import js


def call_internal(parts, args):
    return js.call(js.ref(".".join(["$nope"] + parts)), args)
