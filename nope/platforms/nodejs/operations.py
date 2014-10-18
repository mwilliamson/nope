from . import js
from .internals import call_internal


number = {
    "add": lambda left, right: js.binary_operation("+", left, right),
    "sub": lambda left, right: js.binary_operation("-", left, right),
    "mul": lambda left, right: js.binary_operation("*", left, right),
    "truediv": lambda left, right: js.binary_operation("/", left, right),
    "floordiv": lambda left, right: call_internal(["numberFloor"], [js.binary_operation("/", left, right)]),
    "mod": lambda left, right: call_internal(["numberMod"], [left, right]),
    "divmod": lambda left, right: call_internal(["numberDivMod"], [left, right]),
    "pow": lambda left, right: call_internal(["numberPow"], [left, right]),
    # TODO: raise error on negative shifts
    "lshift": lambda left, right: js.binary_operation("<<", left, right),
    # TODO: raise error on negative shifts
    "rshift": lambda left, right: js.binary_operation(">>", left, right),
    "and": lambda left, right: js.binary_operation("&", left, right),
    "or": lambda left, right: js.binary_operation("|", left, right),
    "xor": lambda left, right: js.binary_operation("^", left, right),
    
    "neg": lambda operand: js.unary_operation("-", operand),
    "pos": lambda operand: js.unary_operation("+", operand),
    "abs": lambda operand: js.call(js.ref("Math.abs"), [operand]),
    "invert": lambda operand: js.unary_operation("~", operand),
    
    "eq": lambda left, right: js.binary_operation("==", left, right),
    "ne": lambda left, right: js.binary_operation("!=", left, right),
    "lt": lambda left, right: js.binary_operation("<", left, right),
    "le": lambda left, right: js.binary_operation("<=", left, right),
    "gt": lambda left, right: js.binary_operation(">", left, right),
    "ge": lambda left, right: js.binary_operation(">=", left, right),
    
    "str": lambda operand: js.call(js.property_access(operand, "toString"), []),
}
