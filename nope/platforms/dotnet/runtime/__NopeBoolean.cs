internal class __NopeBoolean
{
    internal static readonly __NopeBoolean True = new __NopeBoolean(true);
    internal static readonly __NopeBoolean False = new __NopeBoolean(false);
    
    internal static __NopeBoolean Value(bool value)
    {
        return value ? True : False;
    }
    
    private readonly bool _value;
    
    private __NopeBoolean(bool value)
    {
        _value = value;
    }
    
    internal bool __Value { get { return _value; } }
    internal __NopeBoolean __Negate()
    {
        return _value ? False : True;
    }
    
    public __NopeBoolean __bool__()
    {
        return this;
    }
    
    public override string ToString()
    {
        return _value ? "True" : "False";
    }
    
    public __NopeString __str__()
    {
        return __NopeString.Value(ToString());
    }
}
