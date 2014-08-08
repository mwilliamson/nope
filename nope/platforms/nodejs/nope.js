function print(value) {
    console.log(value);
}

function propertyAccess(value, propertyName) {
    if (isString(value) && propertyName === "find") {
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
["add", "sub", "mul", "truediv", "floordiv", "mod", "neg", "pos"].forEach(function(operatorName) {
    operators[operatorName] = function(left, right) {
        if (isNumber(left)) {
            return numberOps[operatorName](left, right);
        } else {
            // TODO: test operator overloading once classes can be defined
            return left["__" + operatorName + "__"](right);
        }
    };
});

var numberOps = {
    add: function(left, right) {
        return left + right;
    },
    sub: function(left, right) {
        return left - right;
    },
    mul: function(left, right) {
        return left * right;
    },
    truediv: function(left, right) {
        return left / right;
    },
    floordiv: function(left, right) {
        return Math.floor(left / right);
    },
    mod: function(left, right) {
        var result = left % right;
        if (result < 0) {
            return result + right;
        } else {
            return result;
        }
    },
    
    neg: function(operand) {
        return -operand;
    },
    pos: function(operand) {
        return operand;
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
    print: print
};

module.exports = {
    propertyAccess: propertyAccess,
    exports: exports,
    operators: operators,
    builtins: builtins
};
