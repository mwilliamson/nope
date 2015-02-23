internal class __NopeTuple
{
    internal static __NopeTuple Values(params dynamic[] values)
    {
        return new __NopeTuple(values);
    }
    
    private readonly dynamic[] _values;
    
    private __NopeTuple(dynamic[] values)
    {
        _values = values;
    }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_values.Length > 0);
    }
    
    public dynamic __getitem__(__NopeInteger key)
    {
        var index = key.__Value;
        return index < 0 ? _values[_values.Length + index] : _values[index];
    }
    
    public override string ToString()
    {
        return "(" + string.Join(", ", System.Linq.Enumerable.Select(_values, value => value.ToString())) + ")";
    }
    
    public __NopeString __str__()
    {
        return __NopeString.Value(ToString());
    }
}
