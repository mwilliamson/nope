function print(value) {
    console.log(value);
}

function propertyAccess(value, propertyName) {
    var methods = builtinMethods[Object.prototype.toString.call(value)];
    if (methods) {
        var method = methods[propertyName];
        if (method === undefined) {
            return method;
        } else {
            return method.bind(value);
        }
    } else {
        // TODO: bind this if the property is a function
        return value[propertyName];
    }
}

function isString(value) {
    return Object.prototype.toString.call(value) === "[object String]";
}

function isArray(value) {
    return Object.prototype.toString.call(value) === "[object Array]";
}

function isNumber(value) {
    return Object.prototype.toString.call(value) === "[object Number]";
}

var operators = {};
["setitem"].forEach(function(operatorName) {
    operators[operatorName] = createMagicTernaryFunction(operatorName);
});
["add", "sub", "mul", "truediv", "floordiv", "mod", "getitem"].forEach(function(operatorName) {
    operators[operatorName] = createMagicBinaryFunction(operatorName);
});

["neg", "pos", "invert"].forEach(function(operatorName) {
    operators[operatorName] = createMagicUnaryFunction(operatorName);
});

var abs = createMagicUnaryFunction("abs");

function createMagicUnaryFunction(operatorName) {
    return function(operand) {
        return propertyAccess(operand, "__" + operatorName + "__")();
    };
}

function createMagicBinaryFunction(operatorName) {
    return function(left, right) {
        return propertyAccess(left, "__" + operatorName + "__")(right);
    };
}

function createMagicTernaryFunction(operatorName) {
    return function(a, b, c) {
        return propertyAccess(a, "__" + operatorName + "__")(b, c);
    };
}

var stringMethods = {
    find: String.prototype.indexOf
};

var arrayMethods = {
    __getitem__: function(slice) {
        // TODO: exceptions
        return this[slice];
    },
    __setitem__: function(slice, value) {
        this[slice] = value;
    },
    __len__: function() {
        return this.length;
    }
};

var builtinMethods = {
    "[object Number]": numberMethods,
    "[object String]": stringMethods,
    "[object Array]": arrayMethods
};

function bool(value) {
    // TODO: add support for __len__ and __iszero__
    var __len__ = propertyAccess(value, "__len__");
    if (__len__ !== undefined) {
        return __len__() > 0;
    }
    
    return !!value;
}

var builtins = {
    bool: bool,
    print: print,
    abs: abs
};

function numberMod(left, right) {
    return (left % right + right) % right;
}

var $nope = module.exports = {
    propertyAccess: propertyAccess,
    exports: exports,
    operators: operators,
    builtins: builtins,
    numberMod: numberMod,
};
