internal class __NopeString
{
    internal static __NopeString Value(string value)
    {
        return new __NopeString(value);
    }
    
    private readonly string _value;
    
    private __NopeString(string value)
    {
        _value = value;
    }
    
    internal string __Value { get { return _value; } }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_value.Length > 0);
    }
    
    public override string ToString()
    {
        return _value;
    }
    
    public __NopeString __str__()
    {
        return __NopeString.Value(ToString());
    }
    
    public __NopeInteger find(__NopeString substring)
    {
        return __NopeInteger.Value(_value.IndexOf(substring._value));
    }
    
    public __NopeString replace(__NopeString old, __NopeString @new)
    {
        return Value(_value.Replace(old._value, @new._value));
    }
}
