function print(value) {
    console.log(value);
}

function propertyAccess(value, propertyName) {
    var methods = builtinMethods[Object.prototype.toString.call(value)];
    if (methods) {
        return methods[propertyName].bind(value);
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

var stringMethods = {
    find: String.prototype.indexOf
};

var arrayMethods = {
    __getitem__: function(slice) {
        // TODO: exceptions
        return this[slice];
    }
};

var builtinMethods = {
    "[object Number]": numberMethods,
    "[object String]": stringMethods,
    "[object Array]": arrayMethods
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

var $nope = module.exports = {
    propertyAccess: propertyAccess,
    exports: exports,
    operators: operators,
    builtins: builtins,
};
