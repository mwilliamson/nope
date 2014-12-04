function print(value) {
    console.log(str(value));
}

function isString(value) {
    return Object.prototype.toString.call(value) == "[object String]";
}

function isFunction(value) {
    return Object.prototype.toString.call(value) == "[object Function]";
}

function getattr(value, propertyName) {
    var methods = builtinMethods[Object.prototype.toString.call(value)];
    if (methods) {
        var method = methods[propertyName];
        if (method === undefined) {
            return method;
        } else {
            return method.bind(value);
        }
    } else if (!(propertyName in value) && propertyName === "__call__" && isFunction(value)) {
        return value;
    } else {
        // TODO: bind this if the property is a function
        return value[propertyName];
    }
}

var operators = {};
["setitem"].forEach(function(operatorName) {
    operators[operatorName] = createMagicTernaryFunction(operatorName);
});
[
    "add", "sub", "mul", "truediv", "floordiv", "mod", "divmod", "pow",
    "lshift", "rshift", "and", "or", "xor",
    "eq", "ne", "lt", "le", "gt", "ge",
    "getitem", "contains"
].forEach(function(operatorName) {
    operators[operatorName] = createMagicBinaryFunction(operatorName);
});

["neg", "pos", "invert"].forEach(function(operatorName) {
    operators[operatorName] = createMagicUnaryFunction(operatorName);
});

var abs = createMagicUnaryFunction("abs");
var divmod = createMagicBinaryFunction("divmod");

function createMagicUnaryFunction(operatorName) {
    return function(operand) {
        return getattr(operand, "__" + operatorName + "__")();
    };
}

function createMagicBinaryFunction(operatorName) {
    return function(left, right) {
        return getattr(left, "__" + operatorName + "__")(right);
    };
}

function createMagicTernaryFunction(operatorName) {
    return function(a, b, c) {
        return getattr(a, "__" + operatorName + "__")(b, c);
    };
}

var stringMethods = {
    find: String.prototype.indexOf,
    __str__: function() {
        return "" + this;
    },
    __eq__: function(other) {
        return isString(other) && this == other;
    }
};

var arrayMethods = {
    __getitem__: function(slice) {
        // TODO: exceptions
        return this[slice];
    },
    __setitem__: function(slice, value) {
        this[slice] = value;
        return null;
    },
    __len__: function() {
        return this.length;
    },
    __iter__: function() {
        var self = this;
        var index = 0
        var end = this.length;
        var iterator = {
            __iter__: function() {
                return self;
            },
            __next__: function() {
                if (index < end) {
                    return self[index++];
                } else {
                    var error = new Error();
                    error.$nopeException = StopIteration();
                    throw error;
                }
            }
        };
        return iterator;
    },
    __contains__: function(value) {
        for (var i = 0; i < this.length; i++) {
            if ($nope.operators.eq(value, this[i])) {
                return true;
            }
        }
        return false;
    },
    __str__: function() {
        return "[" + this.map(str).join(", ") + "]";
    },
    append: function(value) {
        this.push(value);
        return null;
    }
};

var booleanMethods = {
    "__str__": function() {
        return this.valueOf() ? "True" : "False";
    }
};

var noneMethods = {
    "__str__": function() {
        return "None";
    }
};

var builtinMethods = {
    "[object Number]": numberMethods,
    "[object String]": stringMethods,
    "[object Array]": arrayMethods,
    "[object Boolean]": booleanMethods,
    "[object Null]": noneMethods
};

function bool(value) {
    // TODO: add support for __len__ and __iszero__
    var __len__ = getattr(value, "__len__");
    if (__len__ !== undefined) {
        return __len__() > 0;
    }
    
    return !!value;
}

function range(start, end) {
    return {
        __iter__: function() {
            var index = start;
            var iterator = {
                __iter__: function() {
                    return iterator;
                },
                __next__: function() {
                    if (index < end) {
                        return index++;
                    } else {
                        var error = new Error();
                        error.$nopeException = StopIteration();
                        throw error;
                    }
                }
            };
            return iterator;
        }
    };
}

function iter(iterable) {
    return getattr(iterable, "__iter__")();
}

function next(iterable, stopValue) {
    // TODO: support stopValue being undefined i.e. one-arg version of `next`
    try {
        return iterable.__next__();
    } catch (error) {
        if (isinstance(error.$nopeException, StopIteration)) {
            return stopValue;
        } else {
            throw error;
        }
    }
}

function Exception(message) {
    return {
        $nopeType: Exception,
        __str__: function() {
            return str(message);
        }
    };
}

Exception.__name__ = "Exception";
Exception.$baseClasses = [];

// TODO: convert to pure nope
function AssertionError(message) {
    return {
        $nopeType: AssertionError,
        __str__: function() {
            return str(message);
        }
    };
}

AssertionError.__name__ = "AssertionError";
AssertionError.$baseClasses = [Exception];

function StopIteration(message) {
    return {
        $nopeType: StopIteration,
        __str__: function() {
            return str(message);
        }
    };
}

StopIteration.__name__ = "StopIteration";
StopIteration.$baseClasses = [Exception];

function str(value) {
    return getattr(value, "__str__")();
}

function type(value) {
    return value.$nopeType;
}

function tuple(values) {
    var self = {
        __str__: function() {
            return "(" + values.map(str).join(", ") + ")";
        }
    };
    
    for (var i = 0; i < values.length; i++) {
        self[i] = values[i];
    }
    
    return self;
}

function isinstance(obj, clsinfo) {
    // TODO: support primitives (str, number, etc.)
    return issubclass(obj.$nopeType, clsinfo);
}

function issubclass(cls, clsinfo) {
    // TODO: support clsinfo being a tuple
    if (cls === clsinfo) {
        return true;
    }
    
    for (var i = 0; i < cls.$baseClasses.length; i++) {
        if (issubclass(cls.$baseClasses[i], clsinfo)) {
            return true;
        }
    }
    
    return false;
}

var builtins = {
    str: str,
    getattr: getattr,
    bool: bool,
    print: print,
    abs: abs,
    divmod: divmod,
    range: range,
    iter: iter,
    next: next,
    Exception: Exception,
    AssertionError: AssertionError,
    type: type,
    isinstance: isinstance
};

function instanceAttribute(self, attr) {
    if (Object.prototype.toString.call(attr) == "[object Function]") {
        return attr.bind(null, self);
    } else {
        return attr;
    }
}

function numberMod(left, right) {
    return (left % right + right) % right;
}

function numberDivMod(left, right) {
    return tuple([Math.floor(left / right), numberMod(left, right)])
}

var numberPow = Math.pow;

function booleanAnd(left, right) {
    return bool(left) ? right : left;
}

function booleanOr(left, right) {
    return bool(left) ? left : right;
}

var $nope = module.exports = {
    exports: exports,
    operators: operators,
    builtins: builtins,
    
    instanceAttribute: instanceAttribute,
    
    numberMod: numberMod,
    numberDivMod: numberDivMod,
    numberPow: numberPow,
    numberFloor: Math.floor,
    
    booleanAnd: booleanAnd,
    booleanOr: booleanOr,
    
    Error: Error,
    undefined: undefined,
    
    jsArrayToTuple: tuple
};
