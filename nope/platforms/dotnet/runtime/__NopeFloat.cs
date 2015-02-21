internal class __NopeFloat
{
    internal static __NopeFloat Value(double value)
    {
        return new __NopeFloat(value);
    }
    
    private readonly double _value;
    
    private __NopeFloat(double value)
    {
        _value = value;
    }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_value != 0);
    }
    
    public override string ToString()
    {
        return _value.ToString();
    }
}
