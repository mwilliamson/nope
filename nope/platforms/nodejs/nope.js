function print(value) {
    console.log(value);
}

function propertyAccess(value, propertyName) {
    if (isNumber(value)) {
        return numberMethods[propertyName].bind(value);
    } else if (isArray(value)) {
        return arrayMethods[propertyName].bind(value);
    } else if (isString(value) && propertyName === "find") {
        // TODO: perform this rewriting at compile-time
        return value.indexOf.bind(value);
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

var numberMethods = {
    __add__: function(right) {
        return this + right;
    },
    __sub__: function(right) {
        return this - right;
    },
    __mul__: function(right) {
        return this * right;
    },
    __truediv__: function(right) {
        return this / right;
    },
    __floordiv__: function(right) {
        return Math.floor(this / right);
    },
    __mod__: function(right) {
        var result = this % right;
        if (result < 0) {
            return result + right;
        } else {
            return result;
        }
    },
    
    __neg__: function() {
        return -this;
    },
    __pos__: function() {
        return +this;
    },
    __abs__: function() {
        return Math.abs(this);
    },
    __invert__: function() {
        return ~this;
    }
};

var arrayMethods = {
    __getitem__: function(slice) {
        // TODO: exceptions
        return this[slice];
    }
};

function bool(value) {
    // TODO: add support for __len__ and __iszero__
    if (isArray(value)) {
        return value.length > 0;
    }
    
    return !!value;
}

var builtins = {
    bool: bool,
    print: print,
    abs: abs
};

module.exports = {
    propertyAccess: propertyAccess,
    exports: exports,
    operators: operators,
    builtins: builtins
};
