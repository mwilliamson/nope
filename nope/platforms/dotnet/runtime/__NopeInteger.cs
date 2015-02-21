internal class __NopeInteger
{
    internal static __NopeInteger Value(int value)
    {
        return new __NopeInteger(value);
    }
    
    private readonly int _value;
    
    private __NopeInteger(int value)
    {
        _value = value;
    }
    
    internal int __Value { get { return _value; } }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_value != 0);
    }
    
    public __NopeInteger __add__(__NopeInteger other)
    {
        return Value(_value + other._value);
    }
    
    public __NopeInteger __sub__(__NopeInteger other)
    {
        return Value(_value - other._value);
    }
    
    public __NopeInteger __mul__(__NopeInteger other)
    {
        return Value(_value * other._value);
    }
    
    public __NopeFloat __truediv__(__NopeInteger other)
    {
        return __NopeFloat.Value((double)_value / (double)other._value);
    }
    
    public __NopeInteger __floordiv__(__NopeInteger other)
    {
        return __NopeInteger.Value(__floordiv__int(_value, other._value));
    }
    
    private static int __floordiv__int(int left, int right)
    {
        var roundedTowardsZero = left / right;
        var wasRounded = (left % right) != 0;
        
        if (wasRounded && (left < 0 ^ right < 0)) {
            return roundedTowardsZero - 1;
        }
        else
        {
            return roundedTowardsZero;
        }
    }
    
    public __NopeInteger __mod__(__NopeInteger other)
    {
        return Value((_value % other._value + other._value) % other._value);
    }
    
    public __NopeTuple __divmod__(__NopeInteger other)
    {
        return __NopeTuple.Values(
            __floordiv__(other),
            __mod__(other)
        );
    }
    
    public __NopeFloat __pow__(__NopeInteger other)
    {
        return __NopeFloat.Value(System.Math.Pow(_value, other._value));
    }
    
    public __NopeInteger __pos__()
    {
        return this;
    }
    
    public __NopeInteger __neg__()
    {
        return Value(-_value);
    }
    
    public __NopeInteger __abs__()
    {
        return Value(System.Math.Abs(_value));
    }
    
    public __NopeInteger __invert__()
    {
        return Value(~_value);
    }
    
    public __NopeInteger __lshift__(__NopeInteger other)
    {
        return Value(_value << other._value);
    }
    
    public __NopeInteger __rshift__(__NopeInteger other)
    {
        return Value(_value >> other._value);
    }
    
    public __NopeInteger __and__(__NopeInteger other)
    {
        return Value(_value & other._value);
    }
    
    public __NopeInteger __or__(__NopeInteger other)
    {
        return Value(_value | other._value);
    }
    
    public __NopeInteger __xor__(__NopeInteger other)
    {
        return Value(_value ^ other._value);
    }
    
    public __NopeBoolean __eq__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value == other._value);
    }
    
    public __NopeBoolean __ne__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value != other._value);
    }
    
    public __NopeBoolean __le__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value <= other._value);
    }
    
    public __NopeBoolean __lt__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value < other._value);
    }
    
    public __NopeBoolean __ge__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value >= other._value);
    }
    
    public __NopeBoolean __gt__(__NopeInteger other)
    {
        return __NopeBoolean.Value(_value > other._value);
    }
    
    public override string ToString()
    {
        return _value.ToString();
    }
}
